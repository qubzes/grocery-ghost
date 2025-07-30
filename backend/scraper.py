import asyncio
import gzip
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
import urllib3
from bs4 import BeautifulSoup
from pydantic_ai import Agent

from database import SessionLocal
from models import Product, ScrapeSession, SessionStatus
from schemas import PageAnalysis

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = "http://brd-customer-hl_45763da0-zone-grocery_ghost:hez83y11cjt6@brd.superproxy.io:33335"

RELEVANT_PATHS = ["/shop/", "/product/", "/groceries/"]
MODEL_NAME = "google-gla:gemini-2.5-flash-lite-preview-06-17"
SYSTEM_PROMPT = (
    "You are an AI that analyzes grocery store web pages. Given the text content of a page, "
    "determine if it is a product detail page. If yes, extract the product information accurately. "
    "If not, set is_product to false and product to null."
)
gemini_agent = Agent(
    MODEL_NAME,
    system_prompt=SYSTEM_PROMPT,
)


def create_request_session():
    session = requests.Session()
    session.proxies = {"http": PROXY, "https": PROXY}
    session.verify = False
    return session


async def validate_url(url):
    """Validate URL and extract company name using AI"""
    session = create_request_session()
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()

        final_url = response.headers.get("x-unblocker-redirected-to", response.url)
        parsed = urlparse(final_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Get page content for AI analysis
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        clean_text = soup.get_text(separator="\n", strip=True)[
            :2000
        ]  # Limit text for efficiency

        # Use AI to extract company name
        company_prompt = (
            f"Based on this URL ({final_url}) and website content, "
            f"what is the official name of this grocery store company? "
            f"Return only the official company name, nothing else."
        )

        try:
            result = await gemini_agent.run(
                f"{company_prompt}\n\nWebsite content:\n{clean_text}"
            )
            company_name = result.output.strip()
        except Exception as e:
            print(f"Error extracting company name: {e}")
            company_name = parsed.netloc  # Fallback to domain name

        return base_url, parsed.netloc, company_name

    except Exception as e:
        print(f"Error validating URL {url}: {str(e)}")
        raise
    finally:
        session.close()


def find_initial_sitemaps(base_url, session):
    initial_sitemaps = []
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        response = session.get(robots_url)
        response.raise_for_status()
        sitemap_lines = re.findall(
            r"^Sitemap:\s*(.+)$", response.text, re.MULTILINE | re.IGNORECASE
        )
        initial_sitemaps = [
            url.strip() for url in sitemap_lines if url.strip().startswith("http")
        ]
    except Exception:
        pass

    if not initial_sitemaps:
        candidates = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemap-index.xml",
            "/sitemaps.xml",
            "/groceries/sitemap.xml",
            "/shop/sitemaps/sitemap-index.xml",
        ]
        for path in candidates:
            cand = urljoin(base_url, path)
            try:
                response = session.get(cand)
                if response.status_code == 200 and (
                    "xml" in response.headers.get("Content-Type", "").lower()
                    or response.content.startswith(b"<?xml")
                    or response.content.startswith(b"<sitemapindex")
                ):
                    initial_sitemaps.append(cand)
            except Exception:
                pass

    return initial_sitemaps


def fetch_content(url, session):
    try:
        response = session.get(url)
        response.raise_for_status()
        content = response.content
        if content.startswith(b"\x1f\x8b"):
            content = gzip.decompress(content)
        return content
    except Exception:
        return None


def parse_sitemap_content(content, netloc):
    urls = set()
    sub_sitemaps = []
    try:
        root = ET.fromstring(content)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        if root.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}sitemapindex":
            sub_sitemaps = [
                elem.text.replace(".gz", "") if elem.text.endswith(".gz") else elem.text
                for elem in root.findall(".//s:loc", ns)
                if elem.text
            ]
        else:
            for loc in root.findall(".//s:loc", ns):
                if loc.text:
                    loc_url = loc.text.strip()
                    parsed_loc = urlparse(loc_url)
                    if parsed_loc.netloc.lower() == netloc and any(
                        path in parsed_loc.path for path in RELEVANT_PATHS
                    ):
                        urls.add(loc_url)
    except Exception:
        pass
    return urls, sub_sitemaps


def extract_urls_from_sitemaps(initial_sitemaps, netloc, session):
    all_urls = set()
    to_process = initial_sitemaps[:]
    processed = set()

    while to_process:
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {
                executor.submit(fetch_content, url, session): url
                for url in to_process
                if url not in processed
            }
            to_process = []
            for future in as_completed(futures):
                content = future.result()
                url = futures[future]
                if content:
                    urls, sub_sitemaps = parse_sitemap_content(content, netloc)
                    all_urls.update(urls)
                    to_process.extend(
                        [sub for sub in sub_sitemaps if sub not in processed]
                    )
                processed.add(url)

    return all_urls


async def extract_page_data(html, url):
    """Extract page data using Pydantic AI Agent with Gemini"""
    try:
        result = await gemini_agent.run(html, output_type=PageAnalysis)
        return result.output

    except Exception as e:
        print(f"Error extracting data from {url}: {e}")
        return None


async def scrape_single_page(url, session_id, error_log=None):
    """Scrape a single page and return product data if found"""
    request = create_request_session()

    try:
        response = request.get(url, timeout=30)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        clean_html = soup.get_text(separator="\n", strip=True)
        analysis = await extract_page_data(clean_html, url)

        print(f"Analysis for {url}: {analysis}")
        if analysis and analysis.is_product and analysis.product:
            # Return product data instead of immediately saving to DB
            product_data = {
                "session_id": session_id,
                "url": url,
                "name": analysis.product.name,
                "current_price": analysis.product.current_price,
                "original_price": analysis.product.original_price,
                "unit_size": analysis.product.unit_size,
                "image_url": analysis.product.image_url,
                "category": analysis.product.category,
                "dietary_tags": ",".join(analysis.product.dietary_tags)
                if analysis.product.dietary_tags
                else None,
            }
            return product_data

    except requests.exceptions.Timeout as e:
        error_msg = f"Timeout scraping {url}: {str(e)}"
        print(error_msg)
        if error_log is not None:
            error_log.append(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"Request error scraping {url}: {str(e)}"
        print(error_msg)
        if error_log is not None:
            error_log.append(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error scraping {url}: {str(e)}"
        print(error_msg)
        if error_log is not None:
            error_log.append(error_msg)
    finally:
        request.close()

    return None  # Failed


def process_all_pages(urls, session_id):
    """Process all URLs with concurrent workers and batch insert for performance"""
    total_pages = len(urls)
    error_log = []  # Collect errors during scraping
    products_batch = []  # Batch products for bulk insert

    db = SessionLocal()
    scrape_session = (
        db.query(ScrapeSession).filter(ScrapeSession.id == session_id).first()
    )

    if not scrape_session:
        db.close()
        raise ValueError("Session not found")

    def sync_scrape_single_page(url, session_id, error_log):
        return asyncio.run(scrape_single_page(url, session_id, error_log))

    successful_pages = 0
    failed_pages = 0
    products_found = 0

    with ThreadPoolExecutor(
        max_workers=25  # Reduced for better stability and database performance
    ) as executor:
        futures = {
            executor.submit(sync_scrape_single_page, url, session_id, error_log): url
            for url in urls
        }

        for future in as_completed(futures):
            try:
                result = future.result()
                if result:  # If product data was returned
                    products_batch.append(Product(**result))
                    successful_pages += 1
                    products_found += 1
                else:
                    failed_pages += 1
            except Exception as e:
                failed_pages += 1
                error_msg = f"Future failed for URL: {str(e)}"
                error_log.append(error_msg)
                print(error_msg)

            scrape_session.scraped_pages += 1

            # Batch insert products every 10 items for performance
            if len(products_batch) >= 10:
                try:
                    db.add_all(products_batch)
                    db.commit()
                    products_batch = []  # Clear the batch
                except Exception as e:
                    error_msg = f"Database batch insert error: {str(e)}"
                    error_log.append(error_msg)
                    print(error_msg)
                    products_batch = []  # Clear the batch on error

            # Check if we've found 100 products and stop
            if products_found >= 100:
                print("Reached 100 products limit. Cancelling remaining tasks...")

                # Cancel all remaining futures
                for remaining_future in futures:
                    if not remaining_future.done():
                        remaining_future.cancel()

                break

            if scrape_session.scraped_pages % 25 == 0:  # Progress updates
                db.commit()
                print(
                    f"Progress: {scrape_session.scraped_pages}/{total_pages} (Success: {successful_pages}, Failed: {failed_pages}, Products: {products_found})"
                )

    # Insert any remaining products in the batch
    if products_batch:
        try:
            db.add_all(products_batch)
            db.commit()
        except Exception as e:
            error_msg = f"Final batch insert error: {str(e)}"
            error_log.append(error_msg)
            print(error_msg)

    # Save error summary to session if there were errors
    if error_log:
        error_summary = f"Scraping completed with {failed_pages} failures out of {scrape_session.scraped_pages} pages processed.\n\n"
        error_summary += "Error details:\n" + "\n".join(
            error_log[-50:]
        )  # Keep last 50 errors to avoid huge logs

        # Update session with error details
        scrape_session.error = error_summary

    db.commit()
    db.close()

    print(
        f"Scraping summary: {successful_pages} successful, {failed_pages} failed, {products_found} products found"
    )


def scrape_store(session_id: str, base_url: str, netloc: str):
    db = SessionLocal()
    scrape_session = None
    error_details = []

    try:
        scrape_session = (
            db.query(ScrapeSession).filter(ScrapeSession.id == session_id).first()
        )
        if not scrape_session:
            raise ValueError("Session not found")

        request = create_request_session()

        scrape_session.status = SessionStatus.IN_PROGRESS
        db.commit()

        try:
            initial_sitemaps = find_initial_sitemaps(base_url, request)
            if not initial_sitemaps:
                raise ValueError("No sitemaps found.")
        except Exception as e:
            error_msg = f"Error finding sitemaps: {str(e)}"
            error_details.append(error_msg)
            raise ValueError(error_msg)

        try:
            all_urls = extract_urls_from_sitemaps(initial_sitemaps, netloc, request)
        except Exception as e:
            error_msg = f"Error extracting URLs from sitemaps: {str(e)}"
            error_details.append(error_msg)
            raise ValueError(error_msg)

        if not all_urls:
            error_msg = "Couldn't find any relevant product URLs from sitemaps"
            error_details.append(error_msg)
            scrape_session.status = SessionStatus.FAILED
            scrape_session.error = error_msg
            db.commit()
            return

        scrape_session.total_pages = len(all_urls)
        db.commit()

        print(f"Found {len(all_urls)} URLs to process")

        try:
            process_all_pages(list(all_urls), session_id)
        except Exception as e:
            error_msg = f"Error during page processing: {str(e)}"
            error_details.append(error_msg)
            raise

        # Check final product count
        final_product_count = (
            db.query(Product).filter(Product.session_id == session_id).count()
        )

        scrape_session.completed_at = datetime.now(timezone.utc)

        if final_product_count > 0:
            scrape_session.status = SessionStatus.COMPLETED
            print(
                f"Scraping completed successfully with {final_product_count} products found"
            )
        else:
            scrape_session.status = SessionStatus.FAILED
            scrape_session.error = "No products were found during scraping. This may indicate that the website structure is not supported or the product pages could not be identified."

        db.commit()

    except Exception as e:
        error_msg = f"Fatal error during scraping: {str(e)}"
        error_details.append(error_msg)
        print(error_msg)

        if scrape_session:
            scrape_session.status = SessionStatus.FAILED

            # Combine all error details
            if error_details:
                scrape_session.error = (
                    "Scraping failed with the following errors:\n\n"
                    + "\n".join(error_details)
                )
            else:
                scrape_session.error = str(e)

            scrape_session.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        if "request" in locals():
            request.close()
        db.close()

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


async def scrape_single_page(url, session_id):
    """Scrape a single page and return product data if found"""
    db = SessionLocal()
    request = create_request_session()

    try:
        response = request.get(url)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        clean_html = soup.get_text(separator="\n", strip=True)
        print(f"Scraping {url}...")
        print(f"Cleaned HTML length: {len(clean_html)} characters")
        print(f"Cleaned HTML preview: {clean_html[:200]}...")
        analysis = await extract_page_data(clean_html, url)

        print(
            f"Analyzing {url} - is_product: {analysis.is_product if analysis else 'N/A'}"
        )
        print(
            f"Product found: {analysis.product.name if analysis and analysis.is_product and analysis.product else 'No product'}"
        )
        if analysis and analysis.is_product and analysis.product:
            product = Product(
                session_id=session_id,
                url=url,
                name=analysis.product.name,
                current_price=analysis.product.current_price,
                original_price=analysis.product.original_price,
                unit_size=analysis.product.unit_size,
                image_url=analysis.product.image_url,
                category=analysis.product.category,
                dietary_tags=",".join(analysis.product.dietary_tags)
                if analysis.product.dietary_tags
                else None,
            )
            db.add(product)
            db.commit()
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    finally:
        request.close()
        db.close()


def process_all_pages(urls, session_id):
    """Process all URLs with unlimited concurrent workers"""
    total_pages = len(urls)

    db = SessionLocal()
    scrape_session = (
        db.query(ScrapeSession).filter(ScrapeSession.id == session_id).first()
    )

    if not scrape_session:
        db.close()
        raise ValueError("Session not found")

    def sync_scrape_single_page(url, session_id):
        asyncio.run(scrape_single_page(url, session_id))

    with ThreadPoolExecutor(
        max_workers=50
    ) as executor:  # Increased for better concurrency, but limited to prevent overload
        futures = {
            executor.submit(sync_scrape_single_page, url, session_id): url
            for url in urls
        }

        for _ in as_completed(futures):
            scrape_session.scraped_pages += 1

            # Check if we've found 100 products and stop
            product_count = (
                db.query(Product).filter(Product.session_id == session_id).count()
            )
            if product_count >= 100:
                print("Reached 100 products limit. Stopping scraper.")
                break

            if scrape_session.scraped_pages % 50 == 0:  # Commit every 50 pages
                db.commit()
                print(f"Progress: {scrape_session.scraped_pages}/{total_pages}")

    db.commit()
    db.close()


def scrape_store(session_id: str, base_url: str, netloc: str):
    db = SessionLocal()
    scrape_session = None
    try:
        scrape_session = (
            db.query(ScrapeSession).filter(ScrapeSession.id == session_id).first()
        )
        if not scrape_session:
            raise ValueError("Session not found")

        request = create_request_session()

        scrape_session.status = SessionStatus.IN_PROGRESS
        db.commit()

        initial_sitemaps = find_initial_sitemaps(base_url, request)
        if not initial_sitemaps:
            raise ValueError("No sitemaps found.")

        all_urls = extract_urls_from_sitemaps(initial_sitemaps, netloc, request)

        if not all_urls:
            scrape_session.status = SessionStatus.FAILED
            scrape_session.error = "Couldn't find any URLs from sitemaps"
            db.commit()
            return

        scrape_session.total_pages = len(all_urls)
        db.commit()

        process_all_pages(list(all_urls), session_id)

        scrape_session.completed_at = datetime.now(timezone.utc)
        scrape_session.status = SessionStatus.COMPLETED
        db.commit()

    except Exception as e:
        if scrape_session:
            scrape_session.status = SessionStatus.FAILED
            scrape_session.error = str(e)
            db.commit()
    finally:
        db.close()

import gzip
import json
import os
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, urlunparse

import openai
import requests
import urllib3

from database import SessionLocal
from models import Product, ScrapeSession, SessionStatus
from schemas import PageAnalysis

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = "http://brd-customer-hl_3bfca4c1-zone-grocery_ghost:o7hhz0cwt588@brd.superproxy.io:33335"

RELEVANT_PATHS = ["/shop/", "/product/", "/groceries/"]


def create_request_session():
    session = requests.Session()
    session.proxies = {"http": PROXY, "https": PROXY}
    session.verify = False
    return session


def normalize_url(url, request):
    try:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        response = request.head(url, allow_redirects=True, timeout=10)
        final_url = response.url

        parsed = urlparse(final_url)
        base_url = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
        netloc = parsed.netloc.lower()

        return base_url, netloc
    except Exception:
        try:
            parsed = urlparse(url if url.startswith("http") else "https://" + url)
            base_url = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
            netloc = parsed.netloc.lower()
            return base_url, netloc
        except Exception:
            raise ValueError(f"Invalid URL: {url}")


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


def extract_page_data(html, url):
    client = openai.OpenAI(
        base_url="https://api.x.ai/v1", api_key=os.getenv("XAI_API_KEY")
    )
    schema = PageAnalysis.model_json_schema()
    prompt = f"Analyze this HTML from {url} and extract structured data. Output only JSON matching this schema: {json.dumps(schema)}\nHTML: {html[:4000]}"  # Truncate HTML if too long
    try:
        completion = client.chat.completions.create(
            model="grok-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts data from HTML to JSON format.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        json_data = json.loads(completion.choices[0].message.content)
        return PageAnalysis(**json_data)
    except Exception as e:
        print(f"Error extracting data from {url}: {e}")
        return None


def scrape_page(url, session_id, db, request):
    try:
        response = request.get(url)
        response.raise_for_status()
        html = response.text
        analysis = extract_page_data(html, url)
        if analysis and analysis.is_product and analysis.product:
            product_data = analysis.product
            product = Product(
                session_id=session_id,
                url=url,
                name=product_data.name,
                current_price=product_data.current_price,
                original_price=product_data.original_price,
                unit_size=product_data.unit_size,
                image_url=product_data.image_url,
                department=product_data.department,
                dietary_tags=",".join(
                    product_data.dietary_tags
                ),  # Store as comma-separated string
            )
            db.add(product)
            db.commit()
            return 1
        return 0
    except Exception:
        return 0


def scrape_store(session_id: str):
    db = SessionLocal()
    scrape_session = None
    try:
        scrape_session = (
            db.query(ScrapeSession).filter(ScrapeSession.id == session_id).first()
        )
        if not scrape_session:
            raise ValueError("Session not found")

        request = create_request_session()
        base_url, netloc = normalize_url(scrape_session.url, request)

        scrape_session.status = SessionStatus.STARTING
        scrape_session.url = base_url
        db.commit()

        initial_sitemaps = find_initial_sitemaps(base_url, request)
        if not initial_sitemaps:
            raise ValueError("No sitemaps found.")

        all_urls = extract_urls_from_sitemaps(initial_sitemaps, netloc, request)

        scrape_session.total_urls = len(all_urls)
        db.commit()

        print(f"Found {len(all_urls)} relevant URLs. Starting page scraping...")

        # Scrape pages concurrently, update progress
        all_urls_list = list(all_urls)
        batch_size = 100
        for i in range(0, len(all_urls_list), batch_size):
            batch = all_urls_list[i : i + batch_size]
            with ThreadPoolExecutor(
                max_workers=5
            ) as executor:  # Limit concurrency for AI calls
                futures = [
                    executor.submit(scrape_page, url, session_id, db, request)
                    for url in batch
                ]
                for future in as_completed(futures):
                    scraped = future.result()
                    scrape_session.scraped_count += 1 if scraped else 1
            db.commit()
            print(
                f"Progress: {scrape_session.scraped_count}/{scrape_session.total_urls}"
            )

        scrape_session.completed_at = datetime.now(timezone.utc)
        scrape_session.status = SessionStatus.COMPLETED
        db.commit()

    except Exception as e:
        if scrape_session:
            scrape_session.status = SessionStatus.FAILED
            scrape_session.error = str(e)
            db.commit()
        raise
    finally:
        db.close()

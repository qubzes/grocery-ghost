import gzip
import re
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse, urlunparse
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXY = "http://brd-customer-hl_3bfca4c1-zone-grocery_ghost:o7hhz0cwt588@brd.superproxy.io:33335"


def find_initial_sitemaps(base_url, session):
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        response = session.get(robots_url)
        response.raise_for_status()
        sitemap_lines = re.findall(
            r"^Sitemap:\s*(.+)$", response.text, re.MULTILINE | re.IGNORECASE
        )
        sitemaps = [
            url.strip() for url in sitemap_lines if url.strip().startswith("http")
        ]
        if sitemaps:
            return sitemaps
    except Exception as e:
        print(f"Error fetching robots.txt: {e}")

    print("No sitemaps in robots.txt. Trying common locations...")
    candidates = [
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/sitemap-index.xml",
        "/sitemaps.xml",
        "/groceries/sitemap.xml",
        "/shop/sitemaps/sitemap-index.xml",
    ]
    sitemaps = []
    for path in candidates:
        cand = urljoin(base_url, path)
        try:
            response = session.get(cand)
            if response.status_code == 200 and (
                "xml" in response.headers.get("Content-Type", "").lower()
                or response.content.startswith(b"<?xml")
                or response.content.startswith(b"<sitemapindex")
            ):
                sitemaps.append(cand)
        except Exception:
            pass
    return sitemaps


def fetch_content(url, session):
    try:
        response = session.get(url)
        response.raise_for_status()
        content = response.content
        if content.startswith(b"\x1f\x8b"):
            content = gzip.decompress(content)
        return content
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def parse_content(content, netloc):
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
                    if urlparse(loc_url).netloc.lower() == netloc:
                        urls.add(loc_url)
        print(f"Parsed: {len(urls)} URLs, {len(sub_sitemaps)} sub-sitemaps")
        return urls, sub_sitemaps
    except Exception as e:
        print(f"Parse error: {e}")
        return set(), []


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <url>")
        sys.exit(1)

    url_input = sys.argv[1]
    parsed = urlparse(
        url_input if url_input.startswith("http") else "https://" + url_input
    )
    base_url = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
    netloc = parsed.netloc.lower()

    print(f"Extracting sitemap URLs for {base_url}...")

    session = requests.Session()
    session.proxies = {"http": PROXY, "https": PROXY}
    session.verify = False

    initial_sitemaps = find_initial_sitemaps(base_url, session)
    if not initial_sitemaps:
        print("No sitemaps found.")
        sys.exit(0)

    print(f"Processing {len(initial_sitemaps)} initial sitemaps.")
    start_time = time.time()
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
                    urls, subs = parse_content(content, netloc)
                    all_urls.update(urls)
                    to_process.extend([sub for sub in subs if sub not in processed])
                processed.add(url)

    output_file = f"{netloc.replace('.', '_')}_urls.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        for url in sorted(all_urls):
            f.write(url + "\n")

    print(f"Found {len(all_urls)} URLs.")
    print(f"Time: {time.time() - start_time:.2f}s")
    print(f"Saved to {output_file}")

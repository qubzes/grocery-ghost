import requests
import urllib3
import gzip
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TEST_URL = "https://www.costco.com"
PROXY = "http://brd-customer-hl_45763da0-zone-grocery_ghost:hez83y11cjt6@brd.superproxy.io:33335"
RELEVANT_PATHS = ["/shop/", "/product/", "/groceries/", "/items/", "/catalog/"]

def create_session():
    """Create optimized requests session"""
    session = requests.Session()
    session.proxies = {"http": PROXY, "https": PROXY}
    session.verify = False
    session.headers.update({'User-Agent': 'Mozilla/5.0 (compatible; SitemapCrawler/1.0)'})
    return session

def fetch_content(url, session):
    """Safely fetch and decompress content"""
    try:
        response = session.get(url, timeout=60)
        response.raise_for_status()
        
        content = response.content
        if content.startswith(b'\x1f\x8b'):  # gzip
            content = gzip.decompress(content)
        return content.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"✗ Failed to fetch {url}: {e}")
        return None

def discover_sitemaps(base_url, session):
    """Discover all sitemaps from robots.txt and common paths"""
    sitemaps = set()
    
    # Check robots.txt
    robots_url = urljoin(base_url, "/robots.txt")
    content = fetch_content(robots_url, session)
    if content:
        found = re.findall(r"^Sitemap:\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
        sitemaps.update(url.strip() for url in found if url.strip().startswith("http"))
        print(f"✓ Found {len(found)} sitemaps in robots.txt")
    
    # Try common sitemap locations if none found
    if not sitemaps:
        candidates = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml", 
                     "/sitemaps.xml", "/groceries/sitemap.xml"]
        for path in candidates:
            url = urljoin(base_url, path)
            if fetch_content(url, session):
                sitemaps.add(url)
                print(f"✓ Found sitemap at {path}")
                break
    
    return list(sitemaps)

def parse_sitemap(content, target_netloc):
    """Parse sitemap content and extract URLs and sub-sitemaps"""
    if not content:
        return set(), []
    
    try:
        root = ET.fromstring(content)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        
        # Check if it's a sitemap index
        if root.tag.endswith("}sitemapindex") or "sitemapindex" in root.tag:
            sub_sitemaps = []
            for loc in root.findall(".//s:loc", ns) or root.findall(".//loc"):
                if loc.text:
                    # Remove .gz extension for processing
                    url = loc.text.replace(".gz", "") if loc.text.endswith(".gz") else loc.text
                    sub_sitemaps.append(url)
            return set(), sub_sitemaps
        
        # Regular sitemap - extract URLs
        urls = set()
        for loc in root.findall(".//s:loc", ns) or root.findall(".//loc"):
            if loc.text:
                url = loc.text.strip()
                parsed = urlparse(url)
                
                # Filter for relevant URLs from same domain
                if (parsed.netloc.lower() == target_netloc.lower() and 
                    any(path in parsed.path.lower() for path in RELEVANT_PATHS)):
                    urls.add(url)
        
        return urls, []
        
    except ET.ParseError as e:
        print(f"✗ XML parse error: {e}")
        return set(), []

def crawl_all_sitemaps(initial_sitemaps, target_netloc, session):
    """Recursively crawl all sitemaps and extract product URLs"""
    all_urls = set()
    processed = set()
    to_process = initial_sitemaps[:]
    
    while to_process:
        batch = [url for url in to_process if url not in processed]
        to_process = []
        
        print(f"Processing {len(batch)} sitemaps...")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {
                executor.submit(fetch_content, url, session): url 
                for url in batch
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                processed.add(url)
                
                try:
                    content = future.result()
                    if content:
                        urls, sub_sitemaps = parse_sitemap(content, target_netloc)
                        all_urls.update(urls)
                        to_process.extend(sub for sub in sub_sitemaps if sub not in processed)
                        
                        if urls:
                            print(f"✓ {url}: {len(urls)} product URLs")
                        if sub_sitemaps:
                            print(f"✓ {url}: {len(sub_sitemaps)} sub-sitemaps")
                            
                except Exception as e:
                    print(f"✗ Error processing {url}: {e}")
    
    return all_urls

def main():
    """Main execution function"""
    print(f"🚀 Extracting all product URLs from: {TEST_URL}")
    print("=" * 60)
    
    session = create_session()
    parsed_url = urlparse(TEST_URL)
    netloc = parsed_url.netloc
    
    try:
        # Step 1: Discover initial sitemaps
        print("📍 Step 1: Discovering sitemaps...")
        initial_sitemaps = discover_sitemaps(TEST_URL, session)
        
        if not initial_sitemaps:
            print("❌ No sitemaps found!")
            return
        
        print(f"✅ Found {len(initial_sitemaps)} initial sitemap(s)")
        
        # Step 2: Crawl all sitemaps recursively
        print("\n📍 Step 2: Crawling all sitemaps...")
        all_urls = crawl_all_sitemaps(initial_sitemaps, netloc, session)
        
        # Step 3: Save results
        print(f"\n📍 Step 3: Saving results...")
        if all_urls:
            with open("urls.txt", "w", encoding="utf-8") as f:
                f.write(f"Product URLs from {TEST_URL}\n")
                f.write(f"Total URLs: {len(all_urls)}\n")
                f.write("=" * 50 + "\n\n")
                
                for url in sorted(all_urls):
                    f.write(f"{url}\n")
            
            print(f"✅ SUCCESS: {len(all_urls)} unique product URLs saved to urls.txt")
        else:
            print("❌ No relevant product URLs found!")
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        session.close()
        print("\n🏁 Cleanup completed")

if __name__ == "__main__":
    main()
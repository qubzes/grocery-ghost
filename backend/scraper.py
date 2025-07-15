import asyncio
import json
import os
import random
from collections import deque
from urllib.parse import urljoin

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, LLMConfig
from crawl4ai.async_configs import ProxyConfig
from crawl4ai.cache_context import CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from dotenv import load_dotenv

from database import Product, Scrape, SessionLocal
from models import ScrapeSchema

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your-groq-api-key")
GROQ_MODEL = "groq/meta-llama/llama-4-scout-17b-16e-instruct"
PROXY_CONFIG = ProxyConfig(
    server=os.getenv("PROXY_SERVER", "proxy.example.com:8080"),
    username=os.getenv("PROXY_USERNAME", "proxy_username"),
    password=os.getenv("PROXY_PASSWORD", "proxy_password"),
)

PROMPT = """Analyze this grocery store page and extract the following information:

    1. Product Information (if this is a product page):
    - Product name
    - Current price (numeric value only)
    - Original price (numeric value only, if different from current)
    - Unit size (e.g., "12 oz", "1 lb", "500g")
    - Image URL
    - Department/category
    - Dietary tags (e.g., "organic", "gluten-free", "vegan")

    2. URLs: Extract ALL grocery-related URLs from the page (convert to absolute URLs)

    3. Summary: Provide a brief summary of the page content and key findings.

    Rules:
    - If this is NOT a product page, set product to null
    - For prices, extract only numeric values (e.g., "$2.99" becomes 2.99)
    - Include all navigation links, product links, and category links
    - Ensure all URLs are absolute (include domain)"""


async def update_status(session_id: str, status: str, progress: str):
    db = SessionLocal()
    try:
        scrape = db.query(Scrape).filter(Scrape.id == session_id).first()
        scrape.status = status  # type: ignore
        scrape.progress = progress  # type: ignore
        db.commit()
    finally:
        db.close()


async def scrape_task(session_id: str, base_url: str):
    await update_status(session_id, "In Progress", "Initializing...")

    queue = deque([base_url])
    visited = set([base_url])
    products = []
    semaphore = asyncio.Semaphore(3)

    browser_config = BrowserConfig(
        headless=False,
        proxy_config=PROXY_CONFIG
    )
    async with AsyncWebCrawler(config=browser_config, verbose=True) as crawler:

        async def process_url(url):
            async with semaphore:
                extraction_strategy = LLMExtractionStrategy(
                    llm_config=LLMConfig(provider=GROQ_MODEL, api_token=GROQ_API_KEY),
                    schema=ScrapeSchema.model_json_schema(),
                    extraction_type="schema",
                    instruction=PROMPT,
                    input_format="markdown",
                    verbose=True,
                )
                crawler_config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    wait_until="domcontentloaded",
                    page_timeout=180000,
                    extraction_strategy=extraction_strategy,
                )

                try:
                    result = await crawler.arun(url=url, config=crawler_config)
                    result_data = json.loads(result.extracted_content)[0]
                    print("Result Data:", result_data)

                    if "product" in result_data and result_data["product"]:
                        products.append(result_data["product"])
                    if "urls" in result_data:
                        for new_url in result_data["urls"]:
                            absolute_url = urljoin(url, new_url)
                            if absolute_url not in visited:
                                visited.add(absolute_url)
                                queue.append(absolute_url)
                    else:
                        print(f"No URLs found in {url}")
                except Exception as e:
                    print(f"Error processing {url}: {e}")

                await asyncio.sleep(random.uniform(2, 5))

        while queue and len(products) <= 1000:
            current_url = queue.popleft()
            await update_status(
                session_id,
                "In Progress",
                f"Processing {current_url}, queue: {len(queue)}, products: {len(products)}",
            )
            await process_url(current_url)

    # Save to database
    db = SessionLocal()
    try:
        for product_data in products:
            prod = Product(
                scrape_id=session_id,
                name=product_data.get("name"),
                current_price=product_data.get("current_price"),
                original_price=product_data.get("original_price"),
                unit_size=product_data.get("unit_size"),
                image_url=product_data.get("image_url"),
                department=product_data.get("department"),
                dietary_tags=",".join(product_data.get("dietary_tags") or []),
            )
            db.add(prod)
        db.commit()
        await update_status(
            session_id, "Completed", f"Scraped {len(products)} products"
        )
    except Exception as e:
        await update_status(session_id, "Failed", str(e))
    finally:
        db.close()

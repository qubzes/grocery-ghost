import os
import json
import logging
import asyncio
import urllib.request
import ssl
from datetime import datetime
from typing import Optional
from uuid import uuid4
from urllib.parse import urlparse, urljoin

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment variables
PROXY = os.getenv("PROXY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not PROXY:
    raise ValueError("PROXY not set in environment")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set in environment")

# Create proxy opener
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"https": PROXY, "http": PROXY}),
    urllib.request.HTTPSHandler(context=ssl._create_unverified_context()),
)

# SQLAlchemy setup
engine = create_engine("sqlite:///grocery_ghost.db")
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


class DBSession(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    start_url = Column(String, nullable=False)
    status = Column(String, nullable=False)  # pending, running, completed, error
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error = Column(String)


class DBProduct(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    url = Column(String, nullable=False)
    name = Column(String)
    current_price = Column(String)
    original_price = Column(String)
    unit_size = Column(String)
    image_url = Column(String)
    department = Column(String)
    dietary_tags = Column(String)  # JSON serialized list


# Pydantic models for Gemini structured output
class Product(BaseModel):
    name: str = Field(description="Product name")
    current_price: Optional[str] = Field(
        None, description="Current price, include currency"
    )
    original_price: Optional[str] = Field(
        None, description="Original price if discounted"
    )
    unit_size: Optional[str] = Field(None, description="Unit size or quantity")
    image_url: Optional[str] = Field(None, description="Main image URL")
    department: Optional[str] = Field(None, description="Department or category")
    dietary_tags: list[str] = Field(
        default_factory=list, description="Dietary tags like vegan, gluten-free"
    )


class PageAnalysis(BaseModel):
    summary: Optional[str] = Field(
        None, description="A very short summary of the page content"
    )
    is_product: bool = Field(description="Is this a product page?")
    product: Optional[Product] = Field(
        None, description="Product info if it is a product page"
    )


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

# FastAPI app
app = FastAPI(title="Grocery Ghost")


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")


# Helper functions
async def fetch_page_content(url: str) -> str | None:
    try:
        # Run in thread pool to avoid blocking async loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, opener.open, url)
        content = response.read().decode()
        logger.info(f"✓ Fetched content from {url} ({len(content)} chars)")
        return content
    except Exception as e:
        logger.error(f"✗ Fetch error for {url}: {e}")
        return None


def extract_clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def extract_links(html: str, base_url: str, domain: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.netloc == domain and parsed.scheme in ("http", "https"):
            links.add(full_url)
    return links


# Scraper worker with improved logging and worker management
async def scraper_worker(
    worker_id: int,
    queue: asyncio.Queue,
    visited: set[str],
    domain: str,
    session_id: str,
    active_workers: dict,
):
    active_workers[worker_id] = True
    logger.info(f"🚀 Worker {worker_id}: Started")

    processed_count = 0
    product_count = 0

    while True:
        try:
            # Use a longer timeout and check if other workers are still active
            url = await asyncio.wait_for(queue.get(), timeout=30.0)
        except asyncio.TimeoutError:
            # Check if queue is truly empty and no other workers are processing
            if queue.empty():
                logger.info(
                    f"⏰ Worker {worker_id}: Queue timeout - processed {processed_count} pages, found {product_count} products"
                )
                break
            else:
                continue

        processed_count += 1
        logger.info(f"🔄 Worker {worker_id}: Processing page {processed_count} - {url}")

        html = await fetch_page_content(url)
        if not html:
            queue.task_done()
            continue

        text = extract_clean_text(html)
        text_preview = text[:200].replace("\n", " ")
        logger.info(f"📄 Worker {worker_id}: Page content preview: {text_preview}...")

        # Analyze with Gemini
        try:
            prompt = f"Page URL: {url}\nContent:\n{text[:20000]}"  # Truncate if too long for performance
            logger.info(f"🤖 Worker {worker_id}: Sending to Gemini for analysis...")

            result = await gemini_agent.run(prompt, output_type=PageAnalysis)
            analysis = result.output

            logger.info(
                f"📊 Worker {worker_id}: Analysis complete - is_product: {analysis.is_product}, summary: {analysis.summary}"
            )

            if analysis.is_product and analysis.product:
                product = analysis.product
                product_count += 1

                db_product = DBProduct(
                    session_id=session_id,
                    url=url,
                    name=product.name,
                    current_price=product.current_price,
                    original_price=product.original_price,
                    unit_size=product.unit_size,
                    image_url=product.image_url,
                    department=product.department,
                    dietary_tags=json.dumps(product.dietary_tags),
                )
                with SessionLocal() as db:
                    db.add(db_product)
                    db.commit()

                logger.info(
                    f"🛒 Worker {worker_id}: *** PRODUCT FOUND *** '{product.name}' - ${product.current_price} from {url}"
                )
            else:
                logger.info(
                    f"📋 Worker {worker_id}: Not a product page - {analysis.is_product}, {analysis.product}, {analysis.summary}, {url}"
                )

        except Exception as e:
            logger.error(f"❌ Worker {worker_id}: Gemini analysis error for {url}: {e}")

        # Extract and enqueue new links
        new_links = extract_links(html, url, domain)
        added_count = 0
        for link in new_links:
            if link not in visited:
                visited.add(link)
                await queue.put(link)
                added_count += 1

        logger.info(
            f"🔗 Worker {worker_id}: Added {added_count} new links, queue size: {queue.qsize()}"
        )

        queue.task_done()

    active_workers[worker_id] = False
    logger.info(
        f"🏁 Worker {worker_id}: Finished - processed {processed_count} pages, found {product_count} products"
    )


async def run_scraper(session_id: str, start_url: str):
    logger.info(f"🎯 Starting scraper for session {session_id} with URL {start_url}")
    with SessionLocal() as db:
        session = db.query(DBSession).get(session_id)
        session.status = "running"
        db.commit()

    try:
        domain = urlparse(start_url).netloc
        queue = asyncio.Queue()
        visited = set([start_url])
        await queue.put(start_url)

        num_workers = 5  # Reduced number for better tracking
        active_workers = {}

        logger.info(f"🔧 Creating {num_workers} workers for domain {domain}")
        workers = [
            asyncio.create_task(
                scraper_worker(i, queue, visited, domain, session_id, active_workers)
            )
            for i in range(num_workers)
        ]

        # Monitor progress
        start_time = datetime.utcnow()
        while True:
            await asyncio.sleep(60)  # Check every minute

            with SessionLocal() as db:
                product_count = (
                    db.query(DBProduct).filter_by(session_id=session_id).count()
                )

            active_count = sum(1 for active in active_workers.values() if active)
            elapsed = (datetime.utcnow() - start_time).total_seconds() / 60

            logger.info(
                f"📈 Progress Update: {product_count} products found, {active_count} workers active, {queue.qsize()} URLs queued, {elapsed:.1f}min elapsed"
            )

            # Check if all workers are done
            if all(not active for active in active_workers.values()) and queue.empty():
                logger.info("✅ All workers completed, finishing...")
                break

        # Cancel any remaining workers
        for worker in workers:
            if not worker.done():
                worker.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

        with SessionLocal() as db:
            session = db.query(DBSession).get(session_id)
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            db.commit()

            final_count = db.query(DBProduct).filter_by(session_id=session_id).count()

        logger.info(
            f"🎉 Scraper completed for session {session_id} - Found {final_count} total products"
        )

    except Exception as e:
        logger.error(f"💥 Scraper error for session {session_id}: {e}")
        with SessionLocal() as db:
            session = db.query(DBSession).get(session_id)
            session.status = "error"
            session.error = str(e)
            db.commit()


# Endpoints
class ScrapeRequest(BaseModel):
    url: str


@app.post("/scrape")
async def scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid4())
    with SessionLocal() as db:
        new_session = DBSession(id=session_id, start_url=request.url, status="pending")
        db.add(new_session)
        db.commit()
    background_tasks.add_task(run_scraper, session_id, request.url)
    logger.info(f"🚀 Scrape session {session_id} initiated for {request.url}")
    return {"session_id": session_id}


@app.get("/status/{session_id}")
async def status(session_id: str):
    with SessionLocal() as db:
        session = db.query(DBSession).get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        total_products = db.query(DBProduct).filter_by(session_id=session_id).count()
    return {
        "session_id": session_id,
        "status": session.status,
        "start_url": session.start_url,
        "created_at": session.created_at,
        "completed_at": session.completed_at,
        "error": session.error,
        "total_products": total_products,
    }


@app.get("/export/{session_id}")
async def export(session_id: str):
    with SessionLocal() as db:
        session = db.query(DBSession).get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.status != "completed":
            raise HTTPException(status_code=400, detail="Session not completed")
        products = db.query(DBProduct).filter_by(session_id=session_id).all()
    exported = []
    for p in products:
        exported.append(
            {
                "url": p.url,
                "name": p.name,
                "current_price": p.current_price,
                "original_price": p.original_price,
                "unit_size": p.unit_size,
                "image_url": p.image_url,
                "department": p.department,
                "dietary_tags": json.loads(p.dietary_tags) if p.dietary_tags else [],
            }
        )
    return exported

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import ScrapeSession
from schemas import ScrapeRequest
from scraper import scrape_store

router = APIRouter()


@router.post("/scrape")
async def scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    new_session = ScrapeSession(start_url=request.url)
    db.add(new_session)
    db.commit()

    background_tasks.add_task(scrape_store, str(new_session.id), request.url)

    return {"message": f"Scraping started for {request.url}"}

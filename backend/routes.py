from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Product, ScrapeSession
from schemas import ScrapeRequest
from scraper import normalize_url, scrape_store

router = APIRouter()


@router.post("/scrape")
async def scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        base_url, netloc = normalize_url(str(request.url))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    new_session = ScrapeSession(url=base_url)
    db.add(new_session)
    db.commit()

    background_tasks.add_task(scrape_store, str(new_session.id), base_url, netloc)

    return {"message": f"Scraping started for {base_url}", "session_id": new_session.id}


@router.get("/sessions")
async def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ScrapeSession).order_by(ScrapeSession.started_at.desc()).all()

    return {
        "sessions": [
            {
                "id": s.id,
                "url": s.url,
                "status": s.status.value,
                "total_pages": s.total_pages,
                "scraped_pages": s.scraped_pages,
                "started_at": s.started_at,
                "completed_at": s.completed_at,
            }
            for s in sessions
        ]
    }


@router.get("/session/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ScrapeSession).filter(ScrapeSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    products = db.query(Product).filter(Product.session_id == session_id).all()

    response = {
        "session_id": session.id,
        "url": session.url,
        "status": session.status.value,
        "total_pages": session.total_pages,
        "scraped_pages": session.scraped_pages,
        "progress": round((session.scraped_pages / session.total_pages * 100), 2)
        if session.total_pages > 0
        else 0,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
        "error": session.error,
        "total_products": len(products),
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "current_price": p.current_price,
                "original_price": p.original_price,
                "unit_size": p.unit_size,
                "category": p.category,
                "url": p.url,
                "image_url": p.image_url,
                "dietary_tags": p.dietary_tags.split(",") if p.dietary_tags else [],
            }
            for p in products
        ],
    }

    return response

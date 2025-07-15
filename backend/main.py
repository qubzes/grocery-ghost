# main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
import csv
from io import StringIO
from uuid import uuid4

from models import ScrapeRequest, ScrapeStatus
from database import SessionLocal, init_db, Scrape, Product
from scraper import scrape_task

app = FastAPI()

init_db()

@app.post("/scrape")
async def start_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid4())
    db = SessionLocal()
    try:
        scrape = Scrape(id=session_id, url=request.url, status="pending")
        db.add(scrape)
        db.commit()
        background_tasks.add_task(scrape_task, session_id, request.url)
        return {"session_id": session_id}
    finally:
        db.close()

@app.get("/status/{session_id}", response_model=ScrapeStatus)
def get_status(session_id: str):
    db = SessionLocal()
    scrape = db.query(Scrape).get(session_id)
    db.close()
    if not scrape:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": scrape.status, "progress": scrape.progress}

@app.get("/export/{session_id}")
def export_csv(session_id: str):
    db = SessionLocal()
    scrape = db.query(Scrape).get(session_id)
    if not scrape or scrape.status != "Completed":
        db.close()
        raise HTTPException(status_code=400, detail="Scrape not completed or not found")
    
    products = db.query(Product).filter(Product.scrape_id == session_id).all()
    db.close()
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["name", "current_price", "original_price", "unit_size", "image_url", "department", "dietary_tags"])
    writer.writeheader()
    for p in products:
        writer.writerow({
            "name": p.name,
            "current_price": p.current_price,
            "original_price": p.original_price,
            "unit_size": p.unit_size,
            "image_url": p.image_url,
            "department": p.department,
            "dietary_tags": p.dietary_tags
        })
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=products.csv"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import csv
import io
from concurrent.futures import ThreadPoolExecutor

from database import get_db
from models import Product, ScrapeSession, SessionStatus
from schemas import ScrapeRequest
from scraper import validate_url, scrape_store

router = APIRouter()

# Thread pool for database operations
executor = ThreadPoolExecutor(max_workers=4)

# Status mapping for SQLite enum values to frontend expected values
STATUS_MAPPING = {
    "QUEUED": "queued",
    "IN_PROGRESS": "in_progress", 
    "COMPLETED": "completed",
    "FAILED": "failed",
    "CANCELED": "canceled"
}


@router.post("/scrape")
async def scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        base_url, netloc, name = await validate_url(str(request.url))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    new_session = ScrapeSession(url=base_url, name=name)
    db.add(new_session)
    db.commit()

    background_tasks.add_task(scrape_store, str(new_session.id), base_url, netloc)

    return {"message": f"Scraping started for {base_url}", "session_id": new_session.id}


@router.get("/sessions")
async def get_sessions(db: Session = Depends(get_db)):
    """Ultra-optimized sessions endpoint with single query using raw SQL"""
    try:
        # Single optimized query using raw SQL for maximum performance
        query = text("""
            SELECT 
                s.id,
                s.name,
                s.url,
                s.status,
                s.total_pages,
                s.scraped_pages,
                s.started_at,
                s.completed_at,
                s.error,
                COALESCE(p.product_count, 0) as product_count
            FROM sessions s
            LEFT JOIN (
                SELECT session_id, COUNT(*) as product_count
                FROM products
                GROUP BY session_id
            ) p ON s.id = p.session_id
            ORDER BY s.started_at DESC
            LIMIT 50
        """)
        
        result = db.execute(query)
        rows = result.fetchall()
        
        sessions_with_counts = []
        for row in rows:
            sessions_with_counts.append({
                "id": row.id,
                "name": row.name,
                "url": row.url,
                "status": STATUS_MAPPING.get(row.status, row.status.lower()),
                "total_pages": row.total_pages,
                "scraped_pages": row.scraped_pages,
                "started_at": row.started_at,
                "completed_at": row.completed_at,
                "error": row.error,
                "product_count": row.product_count,
            })

        return {"sessions": sessions_with_counts}
    
    except Exception as e:
        print(f"Sessions query error: {str(e)}")
        # Fallback to simpler query if raw SQL fails
        try:
            sessions = db.query(ScrapeSession).order_by(ScrapeSession.started_at.desc()).limit(50).all()
            sessions_with_counts = []
            for s in sessions:
                product_count = db.query(func.count(Product.id)).filter(Product.session_id == s.id).scalar()
                sessions_with_counts.append({
                    "id": s.id,
                    "name": s.name,
                    "url": s.url,
                    "status": s.status.value,
                    "total_pages": s.total_pages,
                    "scraped_pages": s.scraped_pages,
                    "started_at": s.started_at,
                    "completed_at": s.completed_at,
                    "error": s.error,
                    "product_count": product_count or 0,
                })
            return {"sessions": sessions_with_counts}
        except Exception as fallback_e:
            raise HTTPException(status_code=500, detail=f"Error retrieving sessions: {str(fallback_e)}")


@router.get("/session/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Ultra-optimized session detail endpoint with efficient raw SQL"""
    try:
        # Single optimized query to get session details with product count
        session_query = text("""
            SELECT 
                s.id, s.name, s.url, s.status, s.total_pages, s.scraped_pages,
                s.started_at, s.completed_at, s.error,
                COALESCE(p.product_count, 0) as product_count
            FROM sessions s
            LEFT JOIN (
                SELECT session_id, COUNT(*) as product_count
                FROM products
                GROUP BY session_id
            ) p ON s.id = p.session_id
            WHERE s.id = :session_id
        """)
        
        session_result = db.execute(session_query, {"session_id": session_id})
        session_row = session_result.fetchone()
        
        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found")

        product_count = session_row.product_count
        
        # For performance: limit products to first 100 by default
        # This prevents slow responses for large datasets
        products_query = text("""
            SELECT id, name, current_price, original_price, unit_size, 
                   category, url, image_url, dietary_tags
            FROM products 
            WHERE session_id = :session_id 
            ORDER BY name
            LIMIT 100
        """)
        
        products_result = db.execute(products_query, {"session_id": session_id})
        products_rows = products_result.fetchall()

        response = {
            "session_id": session_row.id,
            "name": session_row.name,
            "url": session_row.url,
            "status": STATUS_MAPPING.get(session_row.status, session_row.status.lower()),
            "total_pages": session_row.total_pages,
            "scraped_pages": session_row.scraped_pages,
            "progress": round((session_row.scraped_pages / session_row.total_pages * 100), 2)
            if session_row.total_pages > 0
            else 0,
            "started_at": session_row.started_at,
            "completed_at": session_row.completed_at,
            "error": session_row.error,
            "total_products": product_count,
            "products_shown": len(products_rows),
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
                for p in products_rows
            ],
        }
        
        # Add pagination info if there are more products
        if product_count > 100:
            response["pagination"] = {
                "total_products": product_count,
                "products_shown": len(products_rows),
                "has_more": True,
                "message": f"Showing first {len(products_rows)} of {product_count} products for performance. Use the paginated endpoint for more."
            }

        return response
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"Session detail error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")


@router.get("/session/{session_id}/products")
async def get_session_products_paginated(
    session_id: str, 
    offset: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Paginated products endpoint for large datasets"""
    try:
        # Verify session exists
        session = db.query(ScrapeSession).filter(ScrapeSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get total count
        total_count = db.query(func.count(Product.id)).filter(Product.session_id == session_id).scalar() or 0
        
        # Get paginated products
        products = (
            db.query(Product)
            .filter(Product.session_id == session_id)
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        return {
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
            "pagination": {
                "total": total_count,
                "offset": offset,
                "limit": limit,
                "has_more": offset + limit < total_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving products: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ScrapeSession).filter(ScrapeSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete associated products first
    db.query(Product).filter(Product.session_id == session_id).delete()
    # Delete the session
    db.delete(session)
    db.commit()

    return {"message": "Session deleted successfully"}


@router.get("/session/{session_id}/export")
async def export_session_products(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ScrapeSession).filter(ScrapeSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    products = db.query(Product).filter(Product.session_id == session_id).all()
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Name", "Current Price", "Original Price", "Unit Size", 
        "Category", "URL", "Image URL", "Dietary Tags"
    ])
    
    # Write product data
    for product in products:
        writer.writerow([
            product.name,
            product.current_price,
            product.original_price,
            product.unit_size,
            product.category,
            product.url,
            product.image_url,
            product.dietary_tags
        ])
    
    content = output.getvalue()
    output.close()
    
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={session.name}_products.csv"}
    )

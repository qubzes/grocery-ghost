from pydantic import BaseModel
from typing import List, Optional


class ProductSchema(BaseModel):
    name: str
    current_price: float
    original_price: Optional[float] = None
    unit_size: Optional[str] = None
    image_url: Optional[str] = None
    department: Optional[str] = None
    dietary_tags: Optional[List[str]] = None


class ScrapeSchema(BaseModel):
    product: Optional[ProductSchema] = None
    urls: List[str]
    summary: str


class ScrapeRequest(BaseModel):
    url: str


class ScrapeStatus(BaseModel):
    status: str
    progress: str

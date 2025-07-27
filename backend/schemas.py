from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class ScrapeRequest(BaseModel):
    url: HttpUrl


class ProductSchema(BaseModel):
    name: str = Field(description="Product name")
    current_price: Optional[str] = Field(
        None, description="Current price, include currency"
    )
    original_price: Optional[str] = Field(
        None, description="Original price if discounted"
    )
    unit_size: Optional[str] = Field(None, description="Unit size or quantity")
    category: Optional[str] = Field(None, description="Product category")
    url: str = Field(description="Product page URL")
    image_url: Optional[str] = Field(None, description="Main image URL")
    dietary_tags: list[str] = Field(
        default_factory=list, description="Dietary tags like vegan, gluten-free"
    )


class PageAnalysis(BaseModel):
    is_product: bool = Field(description="Is this a product page?")
    product: Optional[ProductSchema] = Field(
        None, description="Product info if it is a product page"
    )

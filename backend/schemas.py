from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ScrapeRequest(BaseModel):
    url: HttpUrl


class ProductSchema(BaseModel):
    url: str = Field(description="Product page URL")
    name: str = Field(
        description="Extract only the actual product name/title, exclude any promotional text, descriptions, or marketing phrases"
    )
    current_price: Optional[str] = Field(
        None,
        description="Extract only the numeric price with currency symbol (e.g., '$12.99', '€5.50'). Do not include promotional text like 'best price' or 'sale'. If price is in words, convert to numeric format.",
    )
    original_price: Optional[str] = Field(
        None,
        description="Extract only the numeric original/regular price with currency symbol before discount. Must be higher than current_price. Do not include text like 'was' or 'originally'.",
    )
    unit_size: Optional[str] = Field(
        None,
        description="Extract only the quantity, weight, or volume (e.g., '500ml', '2kg', '12 pack'). Do not include product name or descriptions.",
    )
    category: Optional[str] = Field(
        None, description="Extract only the main product category or department name"
    )
    image_url: Optional[str] = Field(
        None,
        description="Extract only the main product image URL, not promotional banners or thumbnails",
    )
    dietary_tags: list[str] = Field(
        default_factory=list,
        description="Extract only specific dietary labels like 'vegan', 'gluten-free', 'organic', 'kosher'. Do not include general descriptions or marketing terms.",
    )


class PageAnalysis(BaseModel):
    is_product: bool = Field(description="Is this a product page?")
    product: Optional[ProductSchema] = Field(
        None, description="Accurate Product info if it is a product page"
    )
    description: Optional[str] = Field(
        None, description="Very brief description of the page content"
    )

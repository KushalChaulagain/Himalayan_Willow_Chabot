import json as _json
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime


class Product(BaseModel):
    """Product model"""
    id: int
    store_id: int = 1
    sku: str
    name: str
    category: str
    subcategory: Optional[str] = None
    description: str
    price: float
    original_price: Optional[float] = None
    in_stock: bool = True
    stock_quantity: int = 0
    rating: float = 0.0
    review_count: int = 0
    sales_count: int = 0
    image_url: Optional[str] = None
    specifications: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("specifications", mode="before")
    @classmethod
    def parse_specifications(cls, v: Any) -> Dict[str, Any]:
        if isinstance(v, str):
            return _json.loads(v)
        if v is None:
            return {}
        return v


class ProductCard(BaseModel):
    """Product card for chat response"""
    id: int
    name: str
    price: float
    image_url: Optional[str] = None
    images: Optional[list] = None
    audio_url: Optional[str] = None
    is_premium: bool = False
    reason: str
    in_stock: bool = True
    specifications: Optional[Dict] = None


class ProductSearchRequest(BaseModel):
    """Product search request"""
    category: Optional[str] = None
    max_price: Optional[float] = None
    min_rating: float = 0.0
    query: Optional[str] = None
    limit: int = 5

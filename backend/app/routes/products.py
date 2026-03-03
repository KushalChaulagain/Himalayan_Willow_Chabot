"""Products API - fetch products by IDs or search with cricket filters."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.db.database import Database, get_db
from app.services.products import ProductService

router = APIRouter(prefix="/api/products", tags=["products"])


def _format_product_card(p) -> dict:
    """Format Product to chat product_card structure."""
    return {
        "id": p.id,
        "name": p.name,
        "price": float(p.price),
        "original_price": float(p.original_price) if p.original_price else None,
        "image_url": p.image_url,
        "images": p.specifications.get("images") if p.specifications else None,
        "audio_url": p.specifications.get("audio_url") if p.specifications else None,
        "is_premium": p.price >= 8000,
        "category": p.category,
        "description": p.description,
        "rating": float(p.rating),
        "review_count": p.review_count,
        "reason": f"Great {p.category} rated {p.rating}/5 by {p.review_count} reviews",
        "in_stock": p.in_stock,
        "specifications": p.specifications,
    }


@router.get("/search")
async def search_products(
    category: Optional[str] = Query(None),
    willow_type: Optional[str] = Query(None),
    weight_min: Optional[int] = Query(None),
    weight_max: Optional[int] = Query(None),
    player_level: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    limit: int = Query(12, le=24),
    db: Database = Depends(get_db),
):
    """Search products with cricket-specific filters."""
    if not db.is_available:
        return {"products": [], "product_cards": []}
    product_service = ProductService(db)
    products = await product_service.search_products(
        category=category,
        max_price=max_price,
        willow_type=willow_type,
        weight_min=weight_min,
        weight_max=weight_max,
        player_level=player_level,
        limit=limit,
    )
    return {
        "products": [{"id": p.id, "name": p.name, "price": p.price, "category": p.category} for p in products],
        "product_cards": [_format_product_card(p) for p in products],
    }


@router.get("")
async def get_products_by_ids(
    ids: str = Query(..., description="Comma-separated product IDs"),
    db: Database = Depends(get_db),
):
    """Return product details for the given IDs (e.g. for cart display)."""
    if not db.is_available:
        return {"products": []}
    try:
        product_ids = [int(x.strip()) for x in ids.split(",") if x.strip()][:50]
    except ValueError:
        return {"products": []}
    if not product_ids:
        return {"products": []}
    product_service = ProductService(db)
    products = await product_service.get_products_by_ids(product_ids)
    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "image_url": p.image_url,
                "category": p.category,
                "in_stock": p.in_stock,
            }
            for p in products
        ]
    }

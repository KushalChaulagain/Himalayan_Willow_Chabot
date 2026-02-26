"""Products API - fetch products by IDs for cart display."""
from fastapi import APIRouter, Depends, Query
from app.db.database import Database, get_db
from app.services.products import ProductService

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
async def get_products_by_ids(
    ids: str = Query(..., description="Comma-separated product IDs"),
    db: Database = Depends(get_db),
):
    """Return product details for the given IDs (e.g. for cart display)."""
    if not db.is_available:
        return {"products": []}
    try:
        product_ids = [int(x.strip()) for x in ids.split(",") if x.strip()]
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

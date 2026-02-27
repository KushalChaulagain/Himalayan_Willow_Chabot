"""
Product-first storefront greeting.

Instead of conversational small-talk, the greeting endpoint returns featured
products immediately -- just like an online menu.  Customers see what's
available the instant they open the chat.
"""

from fastapi import APIRouter, Query, Depends
from datetime import datetime
import random
import structlog

from typing import Optional

from app.db.database import Database, get_db
from app.services.products import ProductService
from app.services.recommendations import RecommendationEngine

logger = structlog.get_logger()
router = APIRouter(prefix="/api/chat", tags=["chat"])

NEPAL_UTC_OFFSET_HOURS = 5.75

# ── Short, action-oriented greetings (1 line max) ────────────────────────

NEW_USER_GREETINGS = [
    "Namaste! Here's our top cricket gear. Saw something you liked online? Send a photo and I'll match it!",
    "Welcome to Himalayan Willow! Browse below or describe what you need — I'll find it fast:",
    "Hey! Here's what's trending. Got a screenshot of a bat or gear you saw? Drop it here and I'll find it for you:",
]

RETURNING_GREETINGS = [
    "Welcome back! Here's what's popular. Need something specific? Just describe it or share a photo:",
    "Good to see you again! Check out our latest picks:",
    "Hey, welcome back! Here's what other players are buying right now:",
]

SEASONAL_BANNERS = {
    "monsoon": "Monsoon sale -- moisture guard kits at 20% off!",
    "cricket_season": "Season is ON! Gear up with our latest arrivals.",
    "festival": "Festive deals -- premium gear at special prices!",
}


def _get_nepal_hour() -> int:
    utc_now = datetime.utcnow()
    return int((utc_now.hour + NEPAL_UTC_OFFSET_HOURS) % 24)


def _get_season_key() -> str | None:
    month = datetime.utcnow().month
    if 6 <= month <= 9:
        return "monsoon"
    if month in (10, 11):
        return "festival"
    if month <= 3 or month >= 10:
        return "cricket_season"
    return None


def _format_product_card(p) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "original_price": float(p.original_price) if p.original_price else None,
        "image_url": p.image_url,
        "images": p.specifications.get("images") if p.specifications else None,
        "audio_url": p.specifications.get("audio_url") if p.specifications else None,
        "is_premium": p.price >= 8000,
        "category": p.category,
        "description": p.description,
        "rating": float(p.rating),
        "review_count": p.review_count,
        "reason": f"Rated {p.rating}/5 by {p.review_count} players",
        "in_stock": p.in_stock,
        "specifications": p.specifications,
    }


CATEGORY_QUICK_REPLIES = [
    "Show me Bats",
    "Balls & Accessories",
    "Protection Gear",
    "Kashmir Willow bats",
    "English Willow bats",
    "Bats for beginners",
]


@router.get("/greeting")
async def get_greeting(
    session_id: str | None = Query(None),
    returning: bool = Query(False),
    user_id: Optional[int] = Query(None),
    cart_item_ids: str | None = Query(None, description="Comma-separated product IDs in cart"),
    db: Database = Depends(get_db),
):
    if returning:
        greeting = random.choice(RETURNING_GREETINGS)
    else:
        greeting = random.choice(NEW_USER_GREETINGS)

    season_key = _get_season_key()
    seasonal_nudge = SEASONAL_BANNERS.get(season_key) if season_key else None

    if seasonal_nudge:
        greeting = f"{greeting}\n\n*{seasonal_nudge}*"

    featured_products = []
    if db.is_available:
        try:
            product_service = ProductService(db)
            rec_engine = RecommendationEngine(db)

            cart_ids: list[int] = []
            if cart_item_ids:
                try:
                    cart_ids = [int(x.strip()) for x in cart_item_ids.split(",") if x.strip()]
                except ValueError:
                    pass

            order_product_ids: list[int] = []
            if user_id:
                try:
                    last_order = await db.fetch_one(
                        """
                        SELECT id FROM orders
                        WHERE user_id = $1 AND status NOT IN ('CANCELLED', 'REFUNDED')
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        user_id,
                    )
                    if last_order:
                        order_items = await db.fetch_all(
                            "SELECT product_id FROM order_items WHERE order_id = $1",
                            last_order["id"],
                        )
                        order_product_ids = [r["product_id"] for r in order_items]
                except Exception as e:
                    logger.warning("greeting_order_lookup_failed", error=str(e))

            product_ids_for_recs = cart_ids or order_product_ids

            if product_ids_for_recs and rec_engine:
                suggestions = await rec_engine.suggest_complementary_products(
                    cart_items=product_ids_for_recs,
                    session_id=session_id or f"greeting-{datetime.utcnow().timestamp()}",
                    max_suggestions=6,
                )
                if suggestions:
                    rec_product_ids = [s["product_id"] for s in suggestions]
                    products = await product_service.get_products_by_ids(rec_product_ids)
                    reason_by_id = {s["product_id"]: s["reason"] for s in suggestions}
                    for p in products:
                        card = _format_product_card(p)
                        if p.id in reason_by_id:
                            card["reason"] = reason_by_id[p.id]
                        featured_products.append(card)

            if not featured_products:
                products = await product_service.get_storefront_mix(limit=6)
                featured_products = [_format_product_card(p) for p in products]

        except Exception as e:
            logger.error("greeting_product_fetch_failed", error=str(e))
            if not featured_products:
                try:
                    products = await ProductService(db).get_storefront_mix(limit=6)
                    featured_products = [_format_product_card(p) for p in products]
                except Exception:
                    pass

    logger.info(
        "storefront_greeting_served",
        returning=returning,
        product_count=len(featured_products),
        season=season_key,
        personalized=bool(cart_ids or order_product_ids),
    )

    return {
        "message": greeting,
        "quick_replies": CATEGORY_QUICK_REPLIES,
        "product_cards": featured_products,
        "is_returning_user": returning,
        "seasonal_nudge": seasonal_nudge,
    }

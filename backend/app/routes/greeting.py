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

from app.db.database import Database, get_db
from app.services.products import ProductService

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
]


@router.get("/greeting")
async def get_greeting(
    session_id: str | None = Query(None),
    returning: bool = Query(False),
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
            products = await product_service.get_storefront_mix(limit=6)
            featured_products = [_format_product_card(p) for p in products]
        except Exception as e:
            logger.error("greeting_product_fetch_failed", error=str(e))

    logger.info(
        "storefront_greeting_served",
        returning=returning,
        product_count=len(featured_products),
        season=season_key,
    )

    return {
        "message": greeting,
        "quick_replies": CATEGORY_QUICK_REPLIES,
        "product_cards": featured_products,
        "is_returning_user": returning,
        "seasonal_nudge": seasonal_nudge,
    }

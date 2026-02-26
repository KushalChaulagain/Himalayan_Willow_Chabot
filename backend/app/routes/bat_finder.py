"""
Bat Finder Quiz endpoint -- accepts quiz answers and returns tailored recommendations
using the existing ConsultativeService.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import structlog

from app.services.consultative import ConsultativeService, get_consultative_service
from app.services.products import ProductService
from app.db.database import Database, get_db, DatabaseUnavailableError

logger = structlog.get_logger()
router = APIRouter(prefix="/api/chat", tags=["chat"])

BUDGET_MAP = {
    "under_3k": (0, 3000),
    "3k_7k": (3000, 7000),
    "7k_15k": (7000, 15000),
    "no_limit": (0, 100000),
}

EDUCATIONAL_CONTENT = {
    "knock_in": {
        "title": "Did You Know? Knock-In Your Bat!",
        "body": (
            "A new cricket bat needs 6-8 hours of knocking-in before match use. "
            "This compresses the willow fibres, hardens the surface, and prevents cracking. "
            "Use a bat mallet, start gently on the face, then gradually increase force. "
            "Apply linseed oil the night before to protect the wood. "
            "Skip this step and you risk damaging your investment on the first ball!"
        ),
        "animationType": "mallet_tap",
    },
    "sweet_spot": {
        "title": "Understanding the Sweet Spot",
        "body": (
            "The sweet spot is the area on the bat face where the ball gets maximum power "
            "with minimum vibration. Heavier bats (1180-1220g) have a larger sweet spot "
            "but require more strength. Lighter bats (1050-1120g) are easier to manoeuvre "
            "but the sweet spot is smaller. Your ideal weight depends on your playing style."
        ),
        "animationType": "sweet_spot_glow",
    },
}

WEIGHT_ADVICE = {
    "light": "Lighter bats (under 1120g) are great for quick footwork and timing-based shots. Ideal for players who rely on placement over power.",
    "balanced": "A balanced weight (1120-1180g) gives you the best of both worlds -- enough power for big shots while maintaining control.",
    "heavy": "Heavier bats (over 1180g) pack serious punch. If you have good technique and strength, a heavier bat extends your sweet spot.",
}


class BatFinderRequest(BaseModel):
    playing_level: str
    surface: str
    budget: str
    weight_preference: Optional[int] = None
    session_id: Optional[str] = None


@router.post("/bat-finder")
async def bat_finder(
    request: BatFinderRequest,
    consultative: ConsultativeService = Depends(get_consultative_service),
    db: Database = Depends(get_db),
):
    user_context = {
        "playing_level": request.playing_level,
        "preferred_surface": request.surface,
        "budget_range": request.budget,
    }

    min_price, max_price = BUDGET_MAP.get(request.budget, (0, 100000))

    product_cards: List[Dict[str, Any]] = []

    if db.is_available:
        try:
            recommendations = await consultative.recommend_with_reasoning(
                user_context, "bat", max_price
            )
            product_cards = [
                {
                    "id": r["product_id"],
                    "name": r["name"],
                    "price": r["price"],
                    "image_url": r.get("image_url"),
                    "rating": r.get("rating"),
                    "reason": r["reason"],
                    "in_stock": True,
                    "specifications": r.get("specifications"),
                    "is_premium": r["price"] >= 8000,
                }
                for r in recommendations
            ]
        except DatabaseUnavailableError:
            pass
        except Exception as e:
            logger.error("bat_finder_recommendation_failed", error=str(e))

    # Weight-specific advice
    weight_msg = ""
    if request.weight_preference:
        if request.weight_preference < 1120:
            weight_msg = WEIGHT_ADVICE["light"]
        elif request.weight_preference <= 1180:
            weight_msg = WEIGHT_ADVICE["balanced"]
        else:
            weight_msg = WEIGHT_ADVICE["heavy"]

    surface_label = {
        "turf": "turf wickets",
        "cement": "cement surfaces",
        "matting": "matting pitches",
        "street": "tape ball on the street",
    }.get(request.surface, request.surface)

    level_label = {
        "beginner": "someone just starting out",
        "club": "a club-level player",
        "professional": "a serious competitive player",
    }.get(request.playing_level, request.playing_level)

    message = (
        f"Based on your profile as {level_label} playing on {surface_label}, "
        f"here are my top picks for you."
    )
    if weight_msg:
        message += f"\n\n{weight_msg}"

    is_beginner = request.playing_level == "beginner"
    educational = EDUCATIONAL_CONTENT["knock_in"] if is_beginner else None

    quick_replies = ["Add to cart", "Tell me more", "Show other options"]
    if is_beginner:
        quick_replies.append("What is knock-in?")

    logger.info(
        "bat_finder_completed",
        level=request.playing_level,
        surface=request.surface,
        budget=request.budget,
        results=len(product_cards),
    )

    return {
        "message": message,
        "product_cards": product_cards,
        "educational_content": educational,
        "quick_replies": quick_replies,
    }

"""
User profile endpoints for personalization (Kit Bag, returning user context).
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import structlog

from app.db.database import Database, get_db, DatabaseUnavailableError

logger = structlog.get_logger()
router = APIRouter(prefix="/api/user", tags=["user"])


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    playing_level: Optional[str] = None
    preferred_surface: Optional[str] = None
    budget_range: Optional[str] = None


@router.get("/profile/{session_id}")
async def get_user_profile(
    session_id: str,
    db: Database = Depends(get_db),
):
    """Return user profile + purchase history for the Kit Bag view."""
    profile: Dict[str, Any] = {"session_id": session_id}
    purchase_history: List[Dict[str, Any]] = []

    if db.is_available:
        try:
            row = await db.fetch_one(
                "SELECT * FROM user_profiles WHERE session_id = $1", session_id
            )
            if row:
                profile.update({
                    "playing_level": row.get("playing_level"),
                    "preferred_surface": row.get("preferred_surface"),
                    "budget_range": row.get("budget_range"),
                    "position": row.get("position"),
                    "age_group": row.get("age_group"),
                })
        except (DatabaseUnavailableError, Exception) as e:
            logger.warning("get_user_profile_db_error", error=str(e))

        try:
            orders = await db.fetch_all(
                """
                SELECT o.order_id, o.created_at, oi.product_name, oi.unit_price,
                       oi.quantity, p.image_url, p.category
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                LEFT JOIN products p ON oi.product_id = p.id
                WHERE o.session_id = $1
                ORDER BY o.created_at DESC
                LIMIT 20
                """,
                session_id,
            )
            for row in orders:
                purchase_history.append({
                    "order_id": row["order_id"],
                    "product_name": row["product_name"],
                    "price": float(row["unit_price"]) / 100,
                    "quantity": row["quantity"],
                    "image_url": row.get("image_url"),
                    "category": row.get("category"),
                    "date": row["created_at"].isoformat(),
                })
        except (DatabaseUnavailableError, Exception) as e:
            logger.warning("get_purchase_history_db_error", error=str(e))

    profile["purchase_history"] = purchase_history
    return profile


@router.put("/profile/{session_id}")
async def update_user_profile(
    session_id: str,
    update: ProfileUpdate,
    db: Database = Depends(get_db),
):
    """Update user profile for personalization."""
    if not db.is_available:
        return {"success": True, "message": "Profile saved locally only (no DB)"}

    try:
        existing = await db.fetch_one(
            "SELECT id FROM user_profiles WHERE session_id = $1", session_id
        )

        if existing:
            await db.execute(
                """
                UPDATE user_profiles
                SET playing_level = COALESCE($2, playing_level),
                    preferred_surface = COALESCE($3, preferred_surface),
                    budget_range = COALESCE($4, budget_range),
                    updated_at = NOW()
                WHERE session_id = $1
                """,
                session_id,
                update.playing_level,
                update.preferred_surface,
                update.budget_range,
            )
        else:
            await db.execute(
                """
                INSERT INTO user_profiles (session_id, playing_level, preferred_surface, budget_range)
                VALUES ($1, $2, $3, $4)
                """,
                session_id,
                update.playing_level,
                update.preferred_surface,
                update.budget_range,
            )

        return {"success": True}
    except Exception as e:
        logger.error("update_user_profile_failed", error=str(e))
        return {"success": False, "message": str(e)}

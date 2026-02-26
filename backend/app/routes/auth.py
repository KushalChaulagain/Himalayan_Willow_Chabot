"""Auth routes for Google OAuth and session management."""
import structlog
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
from typing import Optional

from app.services.auth_service import (
    verify_google_token,
    create_jwt,
    decode_jwt,
    get_or_create_user,
)
from app.db.database import Database, get_db
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


class GoogleAuthRequest(BaseModel):
    credential: str


class LinkSessionRequest(BaseModel):
    session_id: str


async def get_current_user_optional(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Optional[dict]:
    """Extract and validate JWT. Returns user payload or None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    if not token:
        return None
    payload = decode_jwt(token)
    if not payload:
        return None
    user_id = payload.get("user_id")
    if not user_id:
        return None
    return {"id": user_id, "sub": str(user_id)}


@router.post("/google")
@limiter.limit("10/minute")
async def google_auth(
    request: Request,
    body: GoogleAuthRequest,
    db: Database = Depends(get_db),
):
    """
    Exchange Google ID token for JWT and user info.
    Creates or updates user in DB.
    """
    if not body.credential:
        raise HTTPException(status_code=400, detail="Missing credential")

    payload = await verify_google_token(body.credential)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired Google token")

    user = await get_or_create_user(
        db,
        google_id=payload["google_id"],
        email=payload.get("email"),
        full_name=payload.get("name"),
        avatar_url=payload.get("picture"),
    )

    if not user:
        raise HTTPException(status_code=500, detail="Failed to create or fetch user")

    token = create_jwt(user["id"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user.get("email"),
            "name": user.get("full_name"),
            "avatar_url": user.get("avatar_url"),
        },
    }


@router.get("/me")
async def get_me(
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """Return current user if authenticated."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # We only have user_id here - for full user info we'd need to hit DB
    # For session restore, client typically has user from initial login
    return {"id": current_user["id"]}


@router.post("/link-session")
@limiter.limit("10/minute")
async def link_session(
    request: Request,
    body: LinkSessionRequest,
    db: Database = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Link current chat session to authenticated user.
    Call after Google sign-in when user had an existing anonymous session.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not body.session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")

    if not db.is_available:
        return {"success": True, "message": "DB unavailable, session not linked"}

    try:
        await db.execute(
            "UPDATE chat_sessions SET user_id = $1 WHERE session_id = $2",
            current_user["id"],
            body.session_id,
        )
        return {"success": True}
    except Exception as e:
        structlog.get_logger().error("link_session_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to link session")

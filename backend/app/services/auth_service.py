"""Auth service for Google OAuth verification and JWT issuance."""
import httpx
import structlog
from datetime import datetime, timedelta
from typing import Optional
import jwt

from app.config import settings
from app.db.database import Database

logger = structlog.get_logger()

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7
SESSION_TOKEN_EXPIRY_HOURS = 24


async def verify_google_token(id_token: str) -> Optional[dict]:
    """
    Verify Google ID token via tokeninfo API.
    Returns payload with sub (google_id), email, name, picture if valid.
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
                timeout=10.0,
            )
        if resp.status_code != 200:
            logger.warning("google_token_verification_failed", status=resp.status_code)
            return None

        data = resp.json()

        # Validate aud matches our client ID (skip if not configured for dev)
        if settings.google_client_id and data.get("aud") != settings.google_client_id:
            logger.warning("google_token_aud_mismatch", aud=data.get("aud"))
            return None

        return {
            "google_id": data.get("sub"),
            "email": data.get("email"),
            "name": data.get("name"),
            "picture": data.get("picture"),
        }
    except Exception as e:
        logger.error("google_token_verification_error", error=str(e))
        return None


def create_jwt(user_id: int) -> str:
    """Create JWT for authenticated user."""
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRY_DAYS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=JWT_ALGORITHM,
    )


def decode_jwt(token: str) -> Optional[dict]:
    """Decode and validate JWT. Returns payload or None."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[JWT_ALGORITHM],
        )
        return payload
    except jwt.InvalidTokenError:
        return None


def create_session_token(session_id: str) -> str:
    """Create a short-lived JWT for chat session ownership. Used for get_chat_history auth."""
    payload = {
        "session_id": session_id,
        "typ": "session",
        "exp": datetime.utcnow() + timedelta(hours=SESSION_TOKEN_EXPIRY_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> Optional[str]:
    """Decode session token and return session_id if valid."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
        if payload.get("typ") != "session":
            return None
        return payload.get("session_id")
    except jwt.InvalidTokenError:
        return None


async def get_or_create_user(
    db: Database,
    google_id: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> Optional[dict]:
    """
    Get existing user by google_id or create new one.
    Returns user dict with id, email, full_name, avatar_url.
    """
    if not db.is_available:
        logger.warning("get_or_create_user_no_db")
        return None

    try:
        existing = await db.fetch_one(
            "SELECT id, email, full_name, avatar_url FROM users WHERE google_id = $1",
            google_id,
        )

        if existing:
            await db.execute(
                "UPDATE users SET last_login_at = NOW(), email = COALESCE($2, email), full_name = COALESCE($3, full_name), avatar_url = COALESCE($4, avatar_url) WHERE google_id = $1",
                google_id,
                email,
                full_name,
                avatar_url,
            )
            return {
                "id": existing["id"],
                "email": existing["email"] or email,
                "full_name": existing["full_name"] or full_name,
                "avatar_url": existing["avatar_url"] or avatar_url,
            }

        result = await db.fetch_one(
            """
            INSERT INTO users (google_id, email, full_name, avatar_url)
            VALUES ($1, $2, $3, $4)
            RETURNING id, email, full_name, avatar_url
            """,
            google_id,
            email,
            full_name,
            avatar_url,
        )
        return {
            "id": result["id"],
            "email": result["email"],
            "full_name": result["full_name"],
            "avatar_url": result["avatar_url"],
        }
    except Exception as e:
        logger.error("get_or_create_user_failed", error=str(e))
        return None

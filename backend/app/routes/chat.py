from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import StreamingResponse
from app.limiter import limiter
import uuid
import structlog
from datetime import datetime
import json
import re
import asyncio

from app.models.chat import ChatMessageRequest, ChatResponse, ChatSessionCreate
from app.services.llm import LLMService, get_llm_service
from app.services.products import ProductService
from app.services.vector_search import vector_search_service
from app.db.database import Database, get_db, DatabaseUnavailableError
from app.routes.auth import get_current_user_optional
from app.services.auth_service import create_session_token, decode_session_token
from app.config import settings

logger = structlog.get_logger()

# About-us intent: bypass LLM for predictable, concise response (avoids duplication)
ABOUT_US_PATTERNS = [
    "what is himalayan willow",
    "what is himalayan",
    "who are you",
    "about the store",
    "tell me about you",
    "tell me about the store",
    "what do you sell",
    "what does himalayan willow",
    "introduce yourself",
    "who is himalayan willow",
]
ABOUT_US_QUICK_REPLIES = ["Explore Bats", "Explore Balls", "Get Directions"]


def _format_product_card(p) -> dict:
    """Format Product model to chat product_card format."""
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
        "reason": f"Great {p.category} rated {p.rating}/5 by {p.review_count} reviews",
        "in_stock": p.in_stock,
        "specifications": p.specifications,
    }
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/session")
@limiter.limit("60/minute")
async def create_session(
    request: Request,
    body: ChatSessionCreate,
    db: Database = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """Create a new chat session. Works without DB (returns in-memory session ID)."""
    session_id = str(uuid.uuid4())
    user_id = current_user["id"] if current_user else None

    if not db.is_available:
        logger.info("chat_session_created_no_db", session_id=session_id)
        return {
            "success": True,
            "session_id": session_id,
            "session_token": create_session_token(session_id),
            "started_at": datetime.utcnow().isoformat() + "Z",
        }

    query = """
    INSERT INTO chat_sessions (session_id, user_id, store_id)
    VALUES ($1, $2, $3)
    RETURNING session_id, started_at
    """

    try:
        result = await db.fetch_one(query, session_id, user_id, 1)
        logger.info("chat_session_created", session_id=session_id)
        return {
            "success": True,
            "session_id": result["session_id"],
            "session_token": create_session_token(result["session_id"]),
            "started_at": result["started_at"].isoformat(),
        }
    except DatabaseUnavailableError:
        return {
            "success": True,
            "session_id": session_id,
            "session_token": create_session_token(session_id),
            "started_at": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error("session_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.post("/message", response_model=ChatResponse)
@limiter.limit("60/minute")
async def send_message(
    request: Request,
    chat_request: ChatMessageRequest,
    llm_service: LLMService = Depends(get_llm_service),
    db: Database = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """Send a chat message and get response. Works without DB (no persistence)."""
    user_id = current_user["id"] if current_user else None

    # Resolve session ID (create in DB only if DB available)
    if not chat_request.session_id:
        session_id = str(uuid.uuid4())
        if db.is_available:
            try:
                create_query = """
                INSERT INTO chat_sessions (session_id, user_id, store_id)
                VALUES ($1, $2, $3)
                """
                await db.execute(create_query, session_id, user_id, 1)
            except DatabaseUnavailableError:
                pass
    else:
        session_id = chat_request.session_id
        # Link session to user if authenticated
        if db.is_available and user_id:
            try:
                await db.execute(
                    "UPDATE chat_sessions SET user_id = $1 WHERE session_id = $2",
                    user_id,
                    session_id,
                )
            except DatabaseUnavailableError:
                pass

    if db.is_available:
        try:
            save_message_query = """
            INSERT INTO chat_messages (session_id, sender, message)
            VALUES ($1, $2, $3)
            """
            await db.execute(save_message_query, session_id, "user", chat_request.message)
            update_session_query = """
            UPDATE chat_sessions
            SET last_activity_at = NOW(), message_count = message_count + 1
            WHERE session_id = $1
            """
            await db.execute(update_session_query, session_id)
        except DatabaseUnavailableError:
            pass

    message_lower = chat_request.message.lower().strip()
    if any(p in message_lower for p in ABOUT_US_PATTERNS):
        about_message = (
            "Himalayan Willow is Nepal's premier cricket equipment store, located in Kathmandu near the Cricket Stadium. "
            "We offer high-quality cricket gear including bats, balls, and protective equipment."
        )
        if settings.store_maps_url:
            about_message += f" [Get Directions]({settings.store_maps_url}) to visit us today!"
        else:
            about_message += " Visit us today!"
        if db.is_available:
            try:
                await db.execute(
                    "INSERT INTO chat_messages (session_id, sender, message) VALUES ($1, $2, $3)",
                    session_id, "bot", about_message,
                )
            except DatabaseUnavailableError:
                pass
        return ChatResponse(
            message=about_message,
            quick_replies=ABOUT_US_QUICK_REPLIES,
            session_id=session_id,
        )

    # Generate LLM response (always works; uses in-memory history when DB unavailable)
    try:
        llm_response = await llm_service.generate_response(
            chat_request.message,
            session_id
        )
    except Exception as e:
        error_type = type(e).__name__
        error_str = str(e).lower()
        
        logger.error(
            "llm_generation_failed",
            error=str(e),
            error_type=error_type,
            session_id=session_id,
            message_preview=chat_request.message[:100]
        )
        
        # Context-aware error messages based on error type
        if "circuit" in error_str or "breaker" in error_str:
            message = "I'm experiencing high traffic right now. Please wait a moment and try again, or I can show you our popular products."
            quick_replies = ["Wait and retry", "Show popular products", "Talk to human"]
        elif "timeout" in error_str:
            message = "I'm taking longer than usual to respond. This might be due to high demand. Would you like to try again or see our popular items?"
            quick_replies = ["Retry", "Show popular products", "Talk to human"]
        elif "rate" in error_str or "quota" in error_str:
            message = "I'm receiving too many requests right now. Please wait a moment before trying again."
            quick_replies = ["Wait and retry", "Talk to human"]
        else:
            message = "I'm having trouble processing your request. Could you try rephrasing? For example: 'Show me bats under 5000 rupees'"
            quick_replies = ["Show me bats", "Show me gloves", "Talk to human"]
        
        return ChatResponse(
            message=message,
            quick_replies=quick_replies,
            session_id=session_id
        )

    category_keywords = {
        "bat": "bat",
        "ball": "ball",
        "glove": "gloves",
        "pad": "pads",
        "helmet": "helmet",
        "shoe": "shoes",
        "bag": "kit_bag",
    }

    browse_keywords = [
        "all product", "all the product", "every product", "full catalog",
        "everything you have", "products you have", "what do you have",
        "what products", "show me everything", "browse", "catalog",
        "what do you sell", "what you sell", "what's available",
        "your collection", "your products", "your range", "your stock",
        "your inventory", "show all", "list all", "all items",
        "view bats", "view balls", "view protective", "view gear",
        "balls & accessories", "protection gear", "accessories",
    ]

    product_trigger_keywords = list(category_keywords.keys()) + [
        "show", "recommend", "suggest", "find", "search", "looking for",
        "need", "want", "buy", "purchase", "price", "cheap", "budget",
        "expensive", "premium", "best", "product", "equipment", "gear",
        "cricket", "collection",
    ]

    product_cards = None
    quick_replies = None

    is_browse_query = any(kw in message_lower for kw in browse_keywords)
    is_product_query = any(kw in message_lower for kw in product_trigger_keywords)

    if db.is_available and (is_browse_query or is_product_query):
        product_service = ProductService(db)

        category = None
        for kw, cat in category_keywords.items():
            if kw in message_lower:
                category = cat
                break

        if "protective" in message_lower or "protection" in message_lower:
            category = None
            limit = 12

        max_price = None
        price_match = re.search(r'(\d+)\s*(?:k|thousand|rupees|rs|npr)', message_lower)
        if price_match:
            val = float(price_match.group(1))
            if "k" in message_lower or "thousand" in message_lower:
                max_price = val * 1000
            else:
                max_price = val

        willow_type = None
        if "kashmir" in message_lower:
            willow_type = "Kashmir Willow"
        elif "english" in message_lower:
            willow_type = "English Willow"

        player_level = None
        if any(w in message_lower for w in ["beginner", "started", "first bat", "new to cricket"]):
            player_level = "Beginner"
        elif any(w in message_lower for w in ["intermediate", "club", "league"]):
            player_level = "Intermediate"
        elif any(w in message_lower for w in ["pro", "professional", "serious", "competitive"]):
            player_level = "Professional"

        weight_min = weight_max = None
        weight_match = re.search(r'(\d{3,4})\s*[-–]\s*(\d{3,4})\s*g', message_lower)
        if weight_match:
            weight_min, weight_max = int(weight_match.group(1)), int(weight_match.group(2))
        elif re.search(r'(\d{3,4})\s*g', message_lower):
            w = int(re.search(r'(\d{3,4})\s*g', message_lower).group(1))
            weight_min = max(900, w - 50)
            weight_max = min(1500, w + 50)

        limit = 6 if category else 12
        if is_browse_query and not category:
            limit = 20

        products = []

        # Try conversational/semantic search first for natural language queries.
        # Uses full message for embedding similarity (e.g. "bat for power hitting").
        if vector_search_service.is_available:
            try:
                vector_results = vector_search_service.search_products_semantic(
                    query=chat_request.message,
                    max_price=max_price,
                    willow_type=willow_type,
                    player_level=player_level,
                    category=category,
                    limit=limit,
                )
                if vector_results:
                    product_ids = [m["product_id"] for m in vector_results]
                    products = await product_service.get_products_by_ids(product_ids)
                    logger.info(
                        "semantic_search_result",
                        query_preview=chat_request.message[:50],
                        product_count=len(products),
                    )
            except Exception as e:
                logger.warning("semantic_search_fallback", error=str(e))

        if not products:
            try:
                products = await product_service.search_products(
                    category=category,
                    max_price=max_price,
                    willow_type=willow_type,
                    weight_min=weight_min,
                    weight_max=weight_max,
                    player_level=player_level,
                    limit=limit
                )
                logger.info("product_search_result", category=category, count=len(products))
            except DatabaseUnavailableError:
                products = []
            except Exception as e:
                logger.error("product_search_error", error=str(e))
                products = []

        if products:
            product_cards = [_format_product_card(p) for p in products]
            if is_browse_query:
                quick_replies = ["Show me bats", "Show me gloves", "Show me pads", "Show me helmets"]
            else:
                quick_replies = ["Add to cart", "Tell me more", "Show other options"]

    if db.is_available:
        try:
            save_message_query = """
            INSERT INTO chat_messages (session_id, sender, message)
            VALUES ($1, $2, $3)
            """
            await db.execute(
                save_message_query,
                session_id,
                "bot",
                llm_response.get("message", "")
            )
        except DatabaseUnavailableError:
            pass

    return ChatResponse(
        message=llm_response.get("message", ""),
        product_cards=product_cards,
        quick_replies=llm_response.get("quick_replies") or quick_replies or ["Show me bats", "Show me gloves", "Talk to human"],
        session_id=session_id,
        session_token=create_session_token(session_id),
    )


@router.post("/stream")
@limiter.limit("60/minute")
async def stream_message(
    request: Request,
    chat_request: ChatMessageRequest,
    llm_service: LLMService = Depends(get_llm_service),
    db: Database = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Stream chat response using Server-Sent Events (SSE).
    Uses true token-level streaming from the LLM with Gemini->Groq fallback.
    """
    session_id = chat_request.session_id or str(uuid.uuid4())
    message_lower = chat_request.message.lower().strip()

    if any(p in message_lower for p in ABOUT_US_PATTERNS):
        about_message = (
            "Himalayan Willow is Nepal's premier cricket equipment store, located in Kathmandu near the Cricket Stadium. "
            "We offer high-quality cricket gear including bats, balls, and protective equipment."
        )
        if settings.store_maps_url:
            about_message += f" [Get Directions]({settings.store_maps_url}) to visit us today!"
        else:
            about_message += " Visit us today!"

        async def about_us_generator():
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id, 'message': about_message, 'quick_replies': ABOUT_US_QUICK_REPLIES})}\n\n"

        return StreamingResponse(
            about_us_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"

            async for event in llm_service.generate_response_stream(
                chat_request.message,
                session_id,
            ):
                yield f"data: {json.dumps(event)}\n\n"

        except Exception as e:
            logger.error("stream_error", error=str(e), session_id=session_id)
            yield f"data: {json.dumps({'type': 'error', 'message': 'I encountered an error. Please try again.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{session_id}")
@limiter.limit("60/minute")
async def get_chat_history(
    request: Request,
    session_id: str,
    db: Database = Depends(get_db),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """Get chat history for a session. Requires X-Session-Token header (from create_session or send_message response)."""
    if not x_session_token:
        raise HTTPException(status_code=401, detail="X-Session-Token header required")
    decoded = decode_session_token(x_session_token)
    if not decoded or decoded != session_id:
        raise HTTPException(status_code=403, detail="Invalid or expired session token")
    if not db.is_available:
        return {
            "success": True,
            "session_id": session_id,
            "messages": [],
        }

    query = """
    SELECT sender, message, created_at
    FROM chat_messages
    WHERE session_id = $1
    ORDER BY created_at ASC
    """

    try:
        messages = await db.fetch_all(query, session_id)
        return {
            "success": True,
            "session_id": session_id,
            "messages": [
                {
                    "sender": msg["sender"],
                    "message": msg["message"],
                    "timestamp": msg["created_at"].isoformat(),
                }
                for msg in messages
            ],
        }
    except DatabaseUnavailableError:
        return {"success": True, "session_id": session_id, "messages": []}
    except Exception as e:
        logger.error("get_history_failed", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail="Failed to retrieve history")

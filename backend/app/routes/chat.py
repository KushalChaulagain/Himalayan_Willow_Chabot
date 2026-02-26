from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid
import structlog
from datetime import datetime
import json
import re
import asyncio

from app.models.chat import ChatMessageRequest, ChatResponse, ChatSessionCreate
from app.services.llm import LLMService, get_llm_service
from app.services.products import ProductService
from app.db.database import Database, get_db, DatabaseUnavailableError
from app.routes.auth import get_current_user_optional

logger = structlog.get_logger()
router = APIRouter(prefix="/api/chat", tags=["chat"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/session")
async def create_session(
    request: ChatSessionCreate,
    db: Database = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """Create a new chat session. Works without DB (returns in-memory session ID)."""
    session_id = str(uuid.uuid4())
    user_id = current_user["id"] if current_user else (request.user_id or None)

    if not db.is_available:
        logger.info("chat_session_created_no_db", session_id=session_id)
        return {
            "success": True,
            "session_id": session_id,
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
            "started_at": result["started_at"].isoformat(),
        }
    except DatabaseUnavailableError:
        return {
            "success": True,
            "session_id": session_id,
            "started_at": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        logger.error("session_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_request: ChatMessageRequest,
    llm_service: LLMService = Depends(get_llm_service),
    db: Database = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """Send a chat message and get response. Works without DB (no persistence)."""
    print(f"\n[DEBUG] send_message called with message: {chat_request.message[:50]}...")
    
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

    message_lower = chat_request.message.lower()

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
        price_match = re.search(r'(\d+)\s*(?:rupees|rs|npr)', message_lower)
        if price_match:
            max_price = float(price_match.group(1))

        limit = 6 if category else 12
        if is_browse_query and not category:
            limit = 20

        try:
            products = await product_service.search_products(
                category=category,
                max_price=max_price,
                limit=limit
            )
            logger.info("product_search_result", category=category, count=len(products))
        except DatabaseUnavailableError:
            products = []
        except Exception as e:
            logger.error("product_search_error", error=str(e))
            products = []

        if products:
            product_cards = [
                {
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
                for p in products
            ]
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
        session_id=session_id
    )


@router.post("/stream")
async def stream_message(
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
async def get_chat_history(
    session_id: str,
    db: Database = Depends(get_db)
):
    """Get chat history for a session. Returns empty when DB unavailable."""
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

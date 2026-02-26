from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid
import structlog
from datetime import datetime
import json
import asyncio

from app.models.chat import ChatMessageRequest, ChatResponse, ChatSessionCreate
from app.services.llm import LLMService, get_llm_service
from app.services.products import ProductService
from app.db.database import Database, get_db, DatabaseUnavailableError

logger = structlog.get_logger()
router = APIRouter(prefix="/api/chat", tags=["chat"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/session")
async def create_session(
    request: ChatSessionCreate,
    db: Database = Depends(get_db)
):
    """Create a new chat session. Works without DB (returns in-memory session ID)."""
    session_id = str(uuid.uuid4())

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
        result = await db.fetch_one(query, session_id, request.user_id, 1)
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
    db: Database = Depends(get_db)
):
    """Send a chat message and get response. Works without DB (no persistence)."""
    print(f"\n[DEBUG] send_message called with message: {chat_request.message[:50]}...")
    
    # Resolve session ID (create in DB only if DB available)
    if not chat_request.session_id:
        session_id = str(uuid.uuid4())
        if db.is_available:
            try:
                create_query = """
                INSERT INTO chat_sessions (session_id, store_id)
                VALUES ($1, $2)
                """
                await db.execute(create_query, session_id, 1)
            except DatabaseUnavailableError:
                pass
    else:
        session_id = chat_request.session_id

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
    product_keywords = ["bat", "ball", "gloves", "pads", "helmet", "shoes", "bag", "show", "recommend"]

    product_cards = llm_response.get("product_cards")  # From parsed LLM JSON
    quick_replies = llm_response.get("quick_replies")   # From parsed LLM JSON

    # Overlay DB-backed product_cards when we have keyword match (real catalog data)
    if db.is_available and any(keyword in message_lower for keyword in product_keywords):
        product_service = ProductService(db)
        category = None
        if "bat" in message_lower:
            category = "bat"
        elif "ball" in message_lower:
            category = "ball"
        elif "glove" in message_lower:
            category = "gloves"
        elif "pad" in message_lower:
            category = "pads"
        elif "helmet" in message_lower:
            category = "helmet"
        elif "shoe" in message_lower:
            category = "shoes"
        elif "bag" in message_lower:
            category = "kit_bag"

        max_price = None
        import re
        price_match = re.search(r'(\d+)\s*(?:rupees|rs|npr)', message_lower)
        if price_match:
            max_price = float(price_match.group(1))

        try:
            products = await product_service.search_products(
                category=category,
                max_price=max_price,
                limit=3
            )
        except DatabaseUnavailableError:
            products = []
        else:
            if products:
                product_cards = [
                    {
                        "id": p.id,
                        "name": p.name,
                        "price": p.price,
                        "image_url": p.image_url,
                        "reason": f"Great {p.category} with {p.rating}★ rating",
                        "in_stock": p.in_stock
                    }
                    for p in products
                ]
                quick_replies = quick_replies or ["Add to cart", "Tell me more", "Show other options"]

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
        quick_replies=quick_replies or ["Show me bats", "Show me gloves", "Talk to human"],
        session_id=session_id
    )


@router.post("/stream")
async def stream_message(
    chat_request: ChatMessageRequest,
    llm_service: LLMService = Depends(get_llm_service),
    db: Database = Depends(get_db)
):
    """
    Stream chat response using Server-Sent Events (SSE).
    This provides real-time typing effect for better UX.
    """
    session_id = chat_request.session_id or str(uuid.uuid4())
    
    async def event_generator():
        try:
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
            
            # Generate response
            llm_response = await llm_service.generate_response(
                chat_request.message,
                session_id
            )
            
            # Stream the message word by word for typing effect
            message = llm_response.get("message", "")
            words = message.split()
            
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                await asyncio.sleep(0.05)  # Small delay for typing effect
            
            # Send completion event with metadata
            yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id, 'language': llm_response.get('language', 'english')})}\n\n"
            
        except Exception as e:
            logger.error("stream_error", error=str(e), session_id=session_id)
            error_message = "I encountered an error while processing your request."
            yield f"data: {json.dumps({'type': 'error', 'message': error_message})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
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

"""
Enhanced Chat Routes with Sales Intelligence

This module integrates:
- Consultative selling (need-based filtering, progressive disclosure)
- Recommendation engine (upsell, cross-sell, bundles)
- Analytics tracking
- Visual search
"""

from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid
import structlog
from datetime import datetime
import json
import asyncio
from typing import Optional, List

from app.models.chat import ChatMessageRequest, ChatResponse, ChatSessionCreate
from app.services.llm import LLMService, get_llm_service
from app.services.products import ProductService
from app.services.consultative import ConsultativeService, get_consultative_service
from app.services.recommendations import RecommendationEngine, get_recommendation_engine
from app.services.analytics import AnalyticsService, get_analytics_service
from app.services.visual_search import VisualSearchService, get_visual_search_service
from app.db.database import Database, get_db, DatabaseUnavailableError
from app.routes.auth import get_current_user_optional

logger = structlog.get_logger()
router = APIRouter(prefix="/api/chat", tags=["chat"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/message-enhanced", response_model=ChatResponse)
async def send_message_enhanced(
    chat_request: ChatMessageRequest,
    llm_service: LLMService = Depends(get_llm_service),
    consultative_service: ConsultativeService = Depends(get_consultative_service),
    recommendation_engine: RecommendationEngine = Depends(get_recommendation_engine),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    db: Database = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Enhanced chat message endpoint with consultative selling and recommendations.
    
    Features:
    - Consultative selling (progressive disclosure, need-based filtering)
    - Automatic upsell/cross-sell suggestions
    - Analytics tracking
    - LLM action validation
    """
    logger.info("enhanced_message_received", message_preview=chat_request.message[:50])
    
    user_id = current_user["id"] if current_user else None

    # Resolve session ID
    if not chat_request.session_id:
        session_id = str(uuid.uuid4())
        if db.is_available:
            try:
                await db.execute(
                    "INSERT INTO chat_sessions (session_id, user_id, store_id) VALUES ($1, $2, $3)",
                    session_id, user_id, 1
                )
            except DatabaseUnavailableError:
                pass
    else:
        session_id = chat_request.session_id
        if db.is_available and user_id:
            try:
                await db.execute(
                    "UPDATE chat_sessions SET user_id = $1 WHERE session_id = $2",
                    user_id, session_id
                )
            except DatabaseUnavailableError:
                pass
    
    # Save user message
    if db.is_available:
        try:
            await db.execute(
                "INSERT INTO chat_messages (session_id, sender, message) VALUES ($1, $2, $3)",
                session_id, "user", chat_request.message
            )
            await db.execute(
                "UPDATE chat_sessions SET last_activity_at = NOW(), message_count = message_count + 1 WHERE session_id = $1",
                session_id
            )
        except DatabaseUnavailableError:
            pass
    
    # Step 1: Gather user context using consultative service
    try:
        user_context = await consultative_service.gather_user_context(
            session_id,
            chat_request.message,
            chat_request.context or {}
        )
    except Exception as e:
        logger.error("gather_user_context_failed", error=str(e))
        user_context = {}
    
    # Step 2: Check if we need to ask clarifying questions
    next_question = await consultative_service.get_next_question(user_context)
    
    if next_question and not any(keyword in chat_request.message.lower() for keyword in ["show", "recommend", "buy", "add to cart"]):
        question_text, quick_replies = next_question
        
        # Return question without showing products yet
        return ChatResponse(
            message=question_text,
            quick_replies=quick_replies,
            session_id=session_id
        )
    
    # Step 3: Generate LLM response
    try:
        llm_response = await llm_service.generate_response(
            chat_request.message,
            session_id,
            context=user_context
        )
        
        # Validate LLM actions (prevent unauthorized discounts, etc.)
        llm_response = llm_service.validate_llm_actions(llm_response)
        
    except Exception as e:
        logger.error("llm_generation_failed", error=str(e), session_id=session_id)
        return ChatResponse(
            message="I'm having trouble processing your request. Could you try rephrasing?",
            quick_replies=["Show me bats", "Show me gloves", "Talk to human"],
            session_id=session_id
        )
    
    # Step 4: Product recommendations (if user is asking for products)
    message_lower = chat_request.message.lower()
    product_keywords = ["bat", "ball", "gloves", "pads", "helmet", "shoes", "bag", "show", "recommend"]
    
    product_cards = None
    upsell_suggestions = []
    cross_sell_suggestions = []
    bundle_suggestions = []
    
    if db.is_available and any(keyword in message_lower for keyword in product_keywords):
        product_service = ProductService(db)
        
        # Determine category
        category = None
        for cat in ["bat", "ball", "gloves", "pads", "helmet", "shoes", "kit_bag"]:
            if cat in message_lower or cat.replace("_", " ") in message_lower:
                category = cat
                break
        
        # Extract price from message
        import re
        max_price = None
        price_match = re.search(r'(\d+)\s*(?:rupees|rs|npr)', message_lower)
        if price_match:
            max_price = float(price_match.group(1))
        elif user_context.get("budget_range"):
            # Use budget from context
            budget_ranges = {
                "under_3k": 3000,
                "3k_7k": 7000,
                "7k_15k": 15000,
                "no_limit": 100000
            }
            max_price = budget_ranges.get(user_context["budget_range"], 100000)
        
        # Get consultative recommendations with reasoning
        if category:
            try:
                recommendations = await consultative_service.recommend_with_reasoning(
                    user_context,
                    category,
                    max_price
                )
                
                if recommendations:
                    product_cards = [
                        {
                            "id": rec["product_id"],
                            "name": rec["name"],
                            "price": rec["price"],
                            "image_url": rec.get("image_url"),
                            "reason": rec["reason"],
                            "in_stock": True
                        }
                        for rec in recommendations
                    ]
                    
                    # Track recommendations
                    await analytics_service.track_interaction(
                        session_id=session_id,
                        event_type="product_recommended",
                        product_ids=[rec["product_id"] for rec in recommendations],
                        recommendation_type="consultative"
                    )
            except Exception as e:
                logger.error("consultative_recommendations_failed", error=str(e))
    
    # Step 5: Check for cart additions and suggest complementary products
    if "add to cart" in message_lower or "added to cart" in message_lower:
        # Extract product IDs from context (this would come from frontend)
        cart_items = chat_request.context.get("cart_items", []) if chat_request.context else []
        
        if cart_items and db.is_available:
            try:
                # Get cross-sell suggestions
                cross_sell = await recommendation_engine.suggest_complementary_products(
                    cart_items,
                    session_id,
                    max_suggestions=3
                )
                
                if cross_sell:
                    cross_sell_suggestions = cross_sell
                    
                    # Track cross-sell suggestions
                    await analytics_service.track_interaction(
                        session_id=session_id,
                        event_type="cross_sell_suggested",
                        product_ids=[item["product_id"] for item in cross_sell],
                        recommendation_type="cross_sell"
                    )
                
                # Check for bundles
                bundles = await recommendation_engine.find_bundles(cart_items, session_id)
                if bundles:
                    bundle_suggestions = bundles
                    
            except Exception as e:
                logger.error("recommendation_engine_failed", error=str(e))
    
    # Step 6: Save bot response
    if db.is_available:
        try:
            await db.execute(
                "INSERT INTO chat_messages (session_id, sender, message, recommendation_context) VALUES ($1, $2, $3, $4)",
                session_id,
                "bot",
                llm_response.get("message", ""),
                {"product_cards": product_cards, "cross_sell": len(cross_sell_suggestions), "bundles": len(bundle_suggestions)}
            )
        except DatabaseUnavailableError:
            pass
    
    # Step 7: Add cricket expertise tip if relevant
    cricket_advice = ""
    if category:
        cricket_advice = consultative_service.get_cricket_advice(category, user_context)
    
    # Combine message with advice
    final_message = llm_response.get("message", "")
    if cricket_advice:
        final_message += f"\n\n{cricket_advice}"
    
    # Prepare response
    response = ChatResponse(
        message=final_message,
        product_cards=product_cards,
        quick_replies=llm_response.get("quick_replies") or ["Show me more", "Add to cart", "Talk to human"],
        session_id=session_id
    )
    
    # Add upsell/cross-sell suggestions to response if available
    if cross_sell_suggestions:
        # Add cross-sell message
        cross_sell_message = "\n\n🎯 Complete Your Kit:"
        for item in cross_sell_suggestions[:2]:
            cross_sell_message += f"\n• {item['name']} - NPR {item['price']:.0f} ({item['reason']})"
        response.message += cross_sell_message
    
    if bundle_suggestions:
        # Add bundle message
        bundle = bundle_suggestions[0]
        bundle_message = f"\n\n💰 Special Bundle: {bundle['bundle_name']}"
        bundle_message += f"\nSave NPR {bundle['savings']:.0f} ({bundle['discount_percentage']:.0f}% off)"
        response.message += bundle_message
    
    return response


@router.post("/visual-search")
async def visual_search(
    file: UploadFile = File(...),
    category: Optional[str] = None,
    visual_search_service: VisualSearchService = Depends(get_visual_search_service),
    llm_service: LLMService = Depends(get_llm_service),
    db: Database = Depends(get_db),
):
    """
    Visual search endpoint: upload image to find similar products.
    Uses CLIP when available, otherwise falls back to Gemini vision.
    """
    try:
        image_bytes = await file.read()
    except Exception as e:
        logger.error("visual_search_read_file_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")

    similar_products: List[dict] = []

    # Path 1: CLIP-based visual search (when transformers/torch available)
    if visual_search_service.is_available():
        try:
            similar_products = await visual_search_service.find_similar_products(
                image_bytes,
                limit=5,
                category=category
            )
        except DatabaseUnavailableError:
            logger.info("visual_search_clip_db_unavailable_fallback_to_gemini")
            similar_products = []
        except Exception as e:
            logger.warning("visual_search_clip_failed", error=str(e))
            similar_products = []

    # Path 2: Gemini vision (when CLIP unavailable or returned no results)
    if not similar_products and db.is_available:
        try:
            product_service = ProductService(db)
            product_summaries = await product_service.get_products_summary_for_context(
                category=category,
                limit=50
            )
            if product_summaries:
                product_ids = await llm_service.generate_product_recommendations_from_image(
                    image_bytes,
                    product_summaries,
                    category_hint=category,
                    limit=5,
                )
                if product_ids:
                    products = await product_service.get_products_by_ids(product_ids)
                    similar_products = [
                        {
                            "product_id": p.id,
                            "name": p.name,
                            "price": p.price,
                            "image_url": p.image_url,
                            "category": p.category,
                            "rating": p.rating,
                            "reason": "Visually similar cricket equipment",
                        }
                        for p in products
                    ]
        except DatabaseUnavailableError:
            logger.warning("visual_search_gemini_db_unavailable")
        except Exception as e:
            logger.error("visual_search_gemini_failed", error=str(e))

    return {
        "success": True,
        "products": similar_products,
        "count": len(similar_products)
    }


@router.post("/track-cart-action")
async def track_cart_action(
    session_id: str,
    product_id: int,
    action: str,  # "added" or "removed"
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    recommendation_engine: RecommendationEngine = Depends(get_recommendation_engine)
):
    """
    Track cart actions and mark recommendations as accepted.
    
    This endpoint should be called when user adds/removes items from cart.
    """
    try:
        if action == "added":
            # Mark recommendation as accepted if it was recommended
            await recommendation_engine.mark_recommendation_accepted(session_id, product_id)
            
            # Track analytics
            await analytics_service.track_interaction(
                session_id=session_id,
                event_type="product_added_to_cart",
                product_ids=[product_id]
            )
        
        return {
            "success": True,
            "message": f"Cart action '{action}' tracked successfully"
        }
        
    except Exception as e:
        logger.error("track_cart_action_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to track cart action")

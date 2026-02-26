"""
Analytics API Endpoints

Provides endpoints for sales metrics, conversion tracking, and revenue attribution.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date, datetime, timedelta
from typing import Optional
import structlog

from app.services.analytics import AnalyticsService, get_analytics_service
from app.db.database import Database, get_db

logger = structlog.get_logger()
router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/metrics/conversion-lift")
async def get_conversion_lift(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Calculate conversion lift: compare conversion rates of users who
    engaged with chatbot vs those who didn't.
    
    Returns:
    - Chatted users: sessions, conversions, conversion rate, revenue
    - Non-chatted users: conversions, conversion rate, revenue
    - Lift percentage and absolute lift
    """
    # Default to last 30 days if not specified
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    try:
        metrics = await analytics_service.calculate_conversion_lift(start_date, end_date)
        
        return {
            "success": True,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "metrics": metrics
        }
    except Exception as e:
        logger.error("get_conversion_lift_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to calculate conversion lift")


@router.get("/metrics/assisted-aov")
async def get_assisted_aov(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Calculate Average Order Value (AOV) for chat-assisted vs non-assisted orders.
    
    Returns:
    - Chat-assisted: order count, total revenue, AOV
    - Non-assisted: order count, total revenue, AOV
    - AOV lift percentage and absolute lift
    """
    # Default to last 30 days if not specified
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    try:
        metrics = await analytics_service.calculate_assisted_aov(start_date, end_date)
        
        return {
            "success": True,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "metrics": metrics
        }
    except Exception as e:
        logger.error("get_assisted_aov_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to calculate assisted AOV")


@router.get("/metrics/recommendation-effectiveness")
async def get_recommendation_effectiveness(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    recommendation_type: Optional[str] = Query(None, description="Filter by type (consultative, upsell, cross_sell, bundle)"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Calculate effectiveness of product recommendations.
    
    Returns acceptance rate, conversion rate, and revenue impact by recommendation type.
    """
    # Default to last 30 days if not specified
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    try:
        metrics = await analytics_service.get_recommendation_effectiveness(
            start_date, end_date, recommendation_type
        )
        
        return {
            "success": True,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "filter": {
                "recommendation_type": recommendation_type
            },
            "metrics": metrics
        }
    except Exception as e:
        logger.error("get_recommendation_effectiveness_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to calculate recommendation effectiveness")


@router.get("/metrics/conversion-funnel")
async def get_conversion_funnel(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Calculate conversion funnel metrics.
    
    Stages:
    1. Chat initiated
    2. Products viewed
    3. Products added to cart
    4. Checkout initiated
    5. Order completed
    
    Returns stage counts, percentages, and conversion rates between stages.
    """
    # Default to last 30 days if not specified
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    try:
        funnel = await analytics_service.get_conversion_funnel(start_date, end_date)
        
        return {
            "success": True,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "funnel": funnel
        }
    except Exception as e:
        logger.error("get_conversion_funnel_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to calculate conversion funnel")


@router.get("/metrics/cross-sell")
async def get_cross_sell_metrics(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Calculate cross-sell effectiveness metrics.
    
    Returns:
    - Percentage of orders with cross-sell items
    - Revenue from cross-sell
    - Average cross-sell items per order
    """
    # Default to last 30 days if not specified
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    try:
        metrics = await analytics_service.get_cross_sell_metrics(start_date, end_date)
        
        return {
            "success": True,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "metrics": metrics
        }
    except Exception as e:
        logger.error("get_cross_sell_metrics_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to calculate cross-sell metrics")


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get comprehensive dashboard summary with all key metrics.
    
    This endpoint aggregates multiple metrics for a dashboard view.
    """
    # Default to last 30 days if not specified
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    try:
        # Fetch all metrics in parallel
        import asyncio
        
        conversion_lift, assisted_aov, funnel, cross_sell, recommendations = await asyncio.gather(
            analytics_service.calculate_conversion_lift(start_date, end_date),
            analytics_service.calculate_assisted_aov(start_date, end_date),
            analytics_service.get_conversion_funnel(start_date, end_date),
            analytics_service.get_cross_sell_metrics(start_date, end_date),
            analytics_service.get_recommendation_effectiveness(start_date, end_date),
            return_exceptions=True
        )
        
        # Handle any errors in individual metrics
        summary = {
            "success": True,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "conversion_lift": conversion_lift if not isinstance(conversion_lift, Exception) else {"error": str(conversion_lift)},
            "assisted_aov": assisted_aov if not isinstance(assisted_aov, Exception) else {"error": str(assisted_aov)},
            "conversion_funnel": funnel if not isinstance(funnel, Exception) else {"error": str(funnel)},
            "cross_sell": cross_sell if not isinstance(cross_sell, Exception) else {"error": str(cross_sell)},
            "recommendations": recommendations if not isinstance(recommendations, Exception) else {"error": str(recommendations)}
        }
        
        return summary
        
    except Exception as e:
        logger.error("get_dashboard_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate dashboard summary")


@router.post("/track/interaction")
async def track_interaction(
    session_id: str,
    event_type: str,
    product_ids: Optional[list] = None,
    recommendation_type: Optional[str] = None,
    metadata: Optional[dict] = None,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Track user interaction event for analytics.
    
    Event types:
    - product_recommended
    - product_viewed
    - product_added_to_cart
    - checkout_initiated
    - order_completed
    """
    try:
        await analytics_service.track_interaction(
            session_id=session_id,
            event_type=event_type,
            product_ids=product_ids,
            recommendation_type=recommendation_type,
            metadata=metadata
        )
        
        return {
            "success": True,
            "message": "Interaction tracked successfully"
        }
    except Exception as e:
        logger.error("track_interaction_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to track interaction")

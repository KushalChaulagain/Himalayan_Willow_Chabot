"""
Analytics Service for Sales Metrics and Revenue Attribution

This service calculates key sales metrics including:
- Conversion lift (chat users vs non-chat users)
- Assisted Average Order Value (AOV)
- Revenue attribution
- Recommendation effectiveness
- Session analytics
"""

from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
import structlog
from fastapi import Depends
from app.db.database import Database, get_db

logger = structlog.get_logger()


class AnalyticsService:
    """Service for sales analytics and metrics calculation"""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def calculate_conversion_lift(
        self,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Calculate conversion lift: compare conversion rates of users who
        engaged with chatbot vs those who didn't.
        
        Returns:
        {
            "chatted_users": {"sessions": int, "conversions": int, "rate": float},
            "non_chatted_users": {"sessions": int, "conversions": int, "rate": float},
            "lift_percentage": float,
            "lift_absolute": float
        }
        """
        query = """
        WITH chat_sessions_in_period AS (
            SELECT DISTINCT session_id, user_id
            FROM chat_sessions
            WHERE started_at::date BETWEEN $1 AND $2
            AND message_count > 0
        ),
        all_orders AS (
            SELECT 
                o.session_id,
                o.user_id,
                o.total_amount,
                CASE 
                    WHEN o.session_id IN (SELECT session_id FROM chat_sessions_in_period)
                    OR o.user_id IN (SELECT user_id FROM chat_sessions_in_period WHERE user_id IS NOT NULL)
                    THEN 'chatted'
                    ELSE 'no_chat'
                END as user_type
            FROM orders o
            WHERE o.created_at::date BETWEEN $1 AND $2
            AND o.status NOT IN ('CANCELLED', 'REFUNDED')
        ),
        metrics AS (
            SELECT 
                user_type,
                COUNT(DISTINCT COALESCE(session_id, user_id::text)) as conversions,
                SUM(total_amount) as revenue
            FROM all_orders
            GROUP BY user_type
        ),
        session_counts AS (
            SELECT 
                'chatted' as user_type,
                COUNT(DISTINCT session_id) as total_sessions
            FROM chat_sessions_in_period
        )
        SELECT 
            m.user_type,
            COALESCE(m.conversions, 0) as conversions,
            COALESCE(m.revenue, 0) as revenue,
            COALESCE(sc.total_sessions, 0) as total_sessions
        FROM metrics m
        LEFT JOIN session_counts sc ON m.user_type = sc.user_type
        """
        
        try:
            results = await self.db.fetch_all(query, start_date, end_date)
            
            metrics = {
                "chatted_users": {"sessions": 0, "conversions": 0, "rate": 0.0, "revenue": 0},
                "non_chatted_users": {"sessions": 0, "conversions": 0, "rate": 0.0, "revenue": 0},
                "lift_percentage": 0.0,
                "lift_absolute": 0.0
            }
            
            for row in results:
                user_type = row["user_type"]
                conversions = row["conversions"]
                revenue = row["revenue"]
                total_sessions = row.get("total_sessions", 0)
                
                if user_type == "chatted":
                    metrics["chatted_users"]["sessions"] = total_sessions
                    metrics["chatted_users"]["conversions"] = conversions
                    metrics["chatted_users"]["revenue"] = revenue / 100  # Convert from paisa to NPR
                    if total_sessions > 0:
                        metrics["chatted_users"]["rate"] = (conversions / total_sessions) * 100
                else:
                    metrics["non_chatted_users"]["conversions"] = conversions
                    metrics["non_chatted_users"]["revenue"] = revenue / 100
            
            # Calculate lift
            chatted_rate = metrics["chatted_users"]["rate"]
            non_chatted_rate = metrics["non_chatted_users"]["rate"]
            
            if non_chatted_rate > 0:
                metrics["lift_percentage"] = ((chatted_rate - non_chatted_rate) / non_chatted_rate) * 100
                metrics["lift_absolute"] = chatted_rate - non_chatted_rate
            
            logger.info(
                "conversion_lift_calculated",
                start_date=str(start_date),
                end_date=str(end_date),
                lift_percentage=metrics["lift_percentage"]
            )
            
            return metrics
            
        except Exception as e:
            logger.error("calculate_conversion_lift_failed", error=str(e))
            return {
                "chatted_users": {"sessions": 0, "conversions": 0, "rate": 0.0, "revenue": 0},
                "non_chatted_users": {"sessions": 0, "conversions": 0, "rate": 0.0, "revenue": 0},
                "lift_percentage": 0.0,
                "lift_absolute": 0.0,
                "error": str(e)
            }
    
    async def calculate_assisted_aov(
        self,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Calculate Average Order Value (AOV) for chat-assisted vs non-assisted orders.
        
        Returns:
        {
            "chat_assisted": {"orders": int, "total_revenue": float, "aov": float},
            "non_assisted": {"orders": int, "total_revenue": float, "aov": float},
            "aov_lift_percentage": float,
            "aov_lift_absolute": float
        }
        """
        query = """
        WITH chat_sessions_in_period AS (
            SELECT DISTINCT session_id, user_id
            FROM chat_sessions
            WHERE started_at::date BETWEEN $1 AND $2
            AND message_count > 0
        ),
        order_metrics AS (
            SELECT 
                CASE 
                    WHEN o.session_id IN (SELECT session_id FROM chat_sessions_in_period)
                    OR o.user_id IN (SELECT user_id FROM chat_sessions_in_period WHERE user_id IS NOT NULL)
                    THEN 'chat_assisted'
                    ELSE 'non_assisted'
                END as order_type,
                COUNT(*) as order_count,
                SUM(o.total_amount) as total_revenue,
                AVG(o.total_amount) as avg_order_value
            FROM orders o
            WHERE o.created_at::date BETWEEN $1 AND $2
            AND o.status NOT IN ('CANCELLED', 'REFUNDED')
            GROUP BY order_type
        )
        SELECT order_type, order_count, total_revenue, avg_order_value
        FROM order_metrics
        """
        
        try:
            results = await self.db.fetch_all(query, start_date, end_date)
            
            metrics = {
                "chat_assisted": {"orders": 0, "total_revenue": 0.0, "aov": 0.0},
                "non_assisted": {"orders": 0, "total_revenue": 0.0, "aov": 0.0},
                "aov_lift_percentage": 0.0,
                "aov_lift_absolute": 0.0
            }
            
            for row in results:
                order_type = row["order_type"]
                order_count = row["order_count"]
                total_revenue = row["total_revenue"] / 100  # Convert from paisa to NPR
                avg_order_value = row["avg_order_value"] / 100
                
                metrics[order_type] = {
                    "orders": order_count,
                    "total_revenue": total_revenue,
                    "aov": avg_order_value
                }
            
            # Calculate AOV lift
            chat_aov = metrics["chat_assisted"]["aov"]
            non_chat_aov = metrics["non_assisted"]["aov"]
            
            if non_chat_aov > 0:
                metrics["aov_lift_percentage"] = ((chat_aov - non_chat_aov) / non_chat_aov) * 100
                metrics["aov_lift_absolute"] = chat_aov - non_chat_aov
            
            logger.info(
                "assisted_aov_calculated",
                start_date=str(start_date),
                end_date=str(end_date),
                chat_aov=chat_aov,
                non_chat_aov=non_chat_aov,
                lift_percentage=metrics["aov_lift_percentage"]
            )
            
            return metrics
            
        except Exception as e:
            logger.error("calculate_assisted_aov_failed", error=str(e))
            return {
                "chat_assisted": {"orders": 0, "total_revenue": 0.0, "aov": 0.0},
                "non_assisted": {"orders": 0, "total_revenue": 0.0, "aov": 0.0},
                "aov_lift_percentage": 0.0,
                "aov_lift_absolute": 0.0,
                "error": str(e)
            }
    
    async def track_interaction(
        self,
        session_id: str,
        event_type: str,
        product_ids: Optional[List[int]] = None,
        recommendation_type: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Track user interactions for analytics.
        
        Event types:
        - product_recommended
        - product_viewed
        - product_added_to_cart
        - checkout_initiated
        - order_completed
        """
        try:
            # Update session analytics
            query = """
            INSERT INTO session_analytics (session_id, interaction_events)
            VALUES ($1, $2::jsonb)
            ON CONFLICT (session_id) DO UPDATE
            SET interaction_events = session_analytics.interaction_events || $2::jsonb,
                updated_at = NOW()
            """
            
            event_data = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "product_ids": product_ids or [],
                "recommendation_type": recommendation_type,
                "metadata": metadata or {}
            }
            
            # Convert to JSONB array format
            import json
            event_json = json.dumps([event_data])
            
            await self.db.execute(query, session_id, event_json)
            
            logger.info(
                "interaction_tracked",
                session_id=session_id,
                event_type=event_type
            )
            
        except Exception as e:
            logger.error("track_interaction_failed", error=str(e), session_id=session_id)
    
    async def get_recommendation_effectiveness(
        self,
        start_date: date,
        end_date: date,
        recommendation_type: Optional[str] = None
    ) -> Dict:
        """
        Calculate effectiveness of product recommendations.
        
        Returns acceptance rate, conversion rate, and revenue impact.
        """
        query = """
        WITH recommendations AS (
            SELECT 
                pr.recommendation_type,
                COUNT(*) as total_recommendations,
                COUNT(*) FILTER (WHERE pr.accepted = true) as accepted_recommendations,
                ARRAY_AGG(DISTINCT pr.session_id) as session_ids
            FROM product_recommendations pr
            WHERE pr.timestamp::date BETWEEN $1 AND $2
            {type_filter}
            GROUP BY pr.recommendation_type
        ),
        conversions AS (
            SELECT 
                r.recommendation_type,
                COUNT(DISTINCT o.id) as orders_count,
                SUM(o.total_amount) as revenue
            FROM recommendations r
            CROSS JOIN UNNEST(r.session_ids) as session_id
            JOIN orders o ON o.session_id = session_id
            WHERE o.created_at::date BETWEEN $1 AND $2
            AND o.status NOT IN ('CANCELLED', 'REFUNDED')
            GROUP BY r.recommendation_type
        )
        SELECT 
            r.recommendation_type,
            r.total_recommendations,
            r.accepted_recommendations,
            ROUND((r.accepted_recommendations::numeric / NULLIF(r.total_recommendations, 0)) * 100, 2) as acceptance_rate,
            COALESCE(c.orders_count, 0) as orders_count,
            COALESCE(c.revenue, 0) / 100.0 as revenue
        FROM recommendations r
        LEFT JOIN conversions c ON r.recommendation_type = c.recommendation_type
        """
        
        type_filter = ""
        if recommendation_type:
            type_filter = f"AND pr.recommendation_type = '{recommendation_type}'"
        
        query = query.format(type_filter=type_filter)
        
        try:
            results = await self.db.fetch_all(query, start_date, end_date)
            
            effectiveness = []
            for row in results:
                effectiveness.append({
                    "recommendation_type": row["recommendation_type"],
                    "total_recommendations": row["total_recommendations"],
                    "accepted_recommendations": row["accepted_recommendations"],
                    "acceptance_rate": float(row["acceptance_rate"]) if row["acceptance_rate"] else 0.0,
                    "orders_count": row["orders_count"],
                    "revenue": float(row["revenue"])
                })
            
            logger.info(
                "recommendation_effectiveness_calculated",
                start_date=str(start_date),
                end_date=str(end_date),
                types_analyzed=len(effectiveness)
            )
            
            return {"recommendations": effectiveness}
            
        except Exception as e:
            logger.error("get_recommendation_effectiveness_failed", error=str(e))
            return {"recommendations": [], "error": str(e)}
    
    async def get_conversion_funnel(
        self,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Calculate conversion funnel metrics.
        
        Stages:
        1. Chat initiated
        2. Products viewed
        3. Products added to cart
        4. Checkout initiated
        5. Order completed
        """
        query = """
        WITH funnel_stages AS (
            SELECT 
                COUNT(DISTINCT cs.session_id) as chat_initiated,
                COUNT(DISTINCT cs.session_id) FILTER (WHERE cs.products_viewed > 0) as products_viewed,
                COUNT(DISTINCT cs.session_id) FILTER (WHERE cs.cart_items_added > 0) as added_to_cart,
                COUNT(DISTINCT o.session_id) as checkout_initiated,
                COUNT(DISTINCT o.session_id) FILTER (WHERE o.status NOT IN ('PENDING', 'CANCELLED', 'REFUNDED')) as order_completed
            FROM chat_sessions cs
            LEFT JOIN orders o ON cs.session_id = o.session_id
            WHERE cs.started_at::date BETWEEN $1 AND $2
        )
        SELECT chat_initiated, products_viewed, added_to_cart, checkout_initiated, order_completed
        FROM funnel_stages
        """
        
        try:
            result = await self.db.fetch_one(query, start_date, end_date)
            
            if not result:
                return {"stages": [], "conversion_rates": {}}
            
            chat_initiated = result["chat_initiated"]
            products_viewed = result["products_viewed"]
            added_to_cart = result["added_to_cart"]
            checkout_initiated = result["checkout_initiated"]
            order_completed = result["order_completed"]
            
            funnel = {
                "stages": [
                    {"name": "Chat Initiated", "count": chat_initiated, "percentage": 100.0},
                    {
                        "name": "Products Viewed",
                        "count": products_viewed,
                        "percentage": (products_viewed / chat_initiated * 100) if chat_initiated > 0 else 0
                    },
                    {
                        "name": "Added to Cart",
                        "count": added_to_cart,
                        "percentage": (added_to_cart / chat_initiated * 100) if chat_initiated > 0 else 0
                    },
                    {
                        "name": "Checkout Initiated",
                        "count": checkout_initiated,
                        "percentage": (checkout_initiated / chat_initiated * 100) if chat_initiated > 0 else 0
                    },
                    {
                        "name": "Order Completed",
                        "count": order_completed,
                        "percentage": (order_completed / chat_initiated * 100) if chat_initiated > 0 else 0
                    }
                ],
                "conversion_rates": {
                    "view_to_cart": (added_to_cart / products_viewed * 100) if products_viewed > 0 else 0,
                    "cart_to_checkout": (checkout_initiated / added_to_cart * 100) if added_to_cart > 0 else 0,
                    "checkout_to_order": (order_completed / checkout_initiated * 100) if checkout_initiated > 0 else 0,
                    "overall": (order_completed / chat_initiated * 100) if chat_initiated > 0 else 0
                }
            }
            
            logger.info(
                "conversion_funnel_calculated",
                start_date=str(start_date),
                end_date=str(end_date),
                overall_conversion=funnel["conversion_rates"]["overall"]
            )
            
            return funnel
            
        except Exception as e:
            logger.error("get_conversion_funnel_failed", error=str(e))
            return {"stages": [], "conversion_rates": {}, "error": str(e)}
    
    async def get_cross_sell_metrics(
        self,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Calculate cross-sell effectiveness metrics.
        
        Returns percentage of orders with cross-sell items and revenue impact.
        """
        query = """
        WITH orders_with_recommendations AS (
            SELECT DISTINCT
                o.id as order_id,
                o.total_amount,
                o.session_id,
                COUNT(DISTINCT pr.product_id) FILTER (
                    WHERE pr.recommendation_type IN ('cross_sell', 'bundle')
                    AND pr.accepted = true
                ) as cross_sell_items
            FROM orders o
            LEFT JOIN product_recommendations pr ON o.session_id = pr.session_id
            WHERE o.created_at::date BETWEEN $1 AND $2
            AND o.status NOT IN ('CANCELLED', 'REFUNDED')
            GROUP BY o.id, o.total_amount, o.session_id
        )
        SELECT 
            COUNT(*) as total_orders,
            COUNT(*) FILTER (WHERE cross_sell_items > 0) as orders_with_cross_sell,
            SUM(total_amount) FILTER (WHERE cross_sell_items > 0) / 100.0 as cross_sell_revenue,
            AVG(cross_sell_items) FILTER (WHERE cross_sell_items > 0) as avg_cross_sell_items_per_order
        FROM orders_with_recommendations
        """
        
        try:
            result = await self.db.fetch_one(query, start_date, end_date)
            
            if not result:
                return {"cross_sell_rate": 0.0, "orders_with_cross_sell": 0, "total_orders": 0}
            
            total_orders = result["total_orders"]
            orders_with_cross_sell = result["orders_with_cross_sell"]
            cross_sell_revenue = float(result["cross_sell_revenue"]) if result["cross_sell_revenue"] else 0.0
            avg_items = float(result["avg_cross_sell_items_per_order"]) if result["avg_cross_sell_items_per_order"] else 0.0
            
            metrics = {
                "total_orders": total_orders,
                "orders_with_cross_sell": orders_with_cross_sell,
                "cross_sell_rate": (orders_with_cross_sell / total_orders * 100) if total_orders > 0 else 0.0,
                "cross_sell_revenue": cross_sell_revenue,
                "avg_cross_sell_items_per_order": avg_items
            }
            
            logger.info(
                "cross_sell_metrics_calculated",
                start_date=str(start_date),
                end_date=str(end_date),
                cross_sell_rate=metrics["cross_sell_rate"]
            )
            
            return metrics
            
        except Exception as e:
            logger.error("get_cross_sell_metrics_failed", error=str(e))
            return {
                "total_orders": 0,
                "orders_with_cross_sell": 0,
                "cross_sell_rate": 0.0,
                "cross_sell_revenue": 0.0,
                "error": str(e)
            }


def get_analytics_service() -> AnalyticsService:
    """Dependency injection for AnalyticsService"""
    from app.db.database import db
    return AnalyticsService(db)

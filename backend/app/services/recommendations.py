"""
Recommendation Engine for Upselling and Cross-Selling

This service implements intelligent product recommendations including:
- Upsell suggestions (higher-value alternatives)
- Cross-sell suggestions (complementary products)
- Bundle recommendations
- "Complete Your Kit" intelligence
"""

from typing import List, Dict, Optional, Set
import structlog
from fastapi import Depends
from app.db.database import Database, get_db
from app.models.product import Product

logger = structlog.get_logger()


class RecommendationEngine:
    """Engine for product recommendations, upsells, and cross-sells"""
    
    # Cross-sell rules: what products go well together
    CROSS_SELL_RULES = {
        "bat": ["batting_gloves", "bat_grip", "scuff_sheet", "knocking_oil", "bat_cover"],
        "batting_gloves": ["bat", "pads", "helmet", "thigh_guard", "inner_gloves"],
        "pads": ["batting_gloves", "helmet", "thigh_guard", "abdominal_guard", "knee_roll"],
        "helmet": ["batting_gloves", "pads", "neck_guard", "helmet_bag"],
        "ball": ["ball_box", "practice_stumps", "bowling_machine", "pitch_roller"],
        "shoes": ["cricket_socks", "shoe_bag", "shoe_cleaner", "insoles"],
        "kit_bag": ["bat_cover", "shoe_bag", "water_bottle", "towel"],
        "gloves": ["bat", "pads", "helmet"],  # Alias for batting_gloves
        "wicket_keeping_gloves": ["wicket_keeping_pads", "inner_gloves", "helmet"],
        "wicket_keeping_pads": ["wicket_keeping_gloves", "abdominal_guard", "helmet"]
    }
    
    # Complete kit templates for different player types
    COMPLETE_KIT_TEMPLATES = {
        "batsman": {
            "essential": ["bat", "batting_gloves", "pads", "helmet"],
            "recommended": ["thigh_guard", "abdominal_guard", "shoes", "kit_bag"],
            "optional": ["bat_grip", "scuff_sheet", "arm_guard", "chest_guard"]
        },
        "bowler": {
            "essential": ["ball", "shoes"],
            "recommended": ["batting_gloves", "pads", "helmet", "kit_bag"],
            "optional": ["wrist_band", "ankle_support", "knee_support"]
        },
        "wicket_keeper": {
            "essential": ["wicket_keeping_gloves", "wicket_keeping_pads", "helmet"],
            "recommended": ["inner_gloves", "abdominal_guard", "shoes", "kit_bag"],
            "optional": ["neck_guard", "chest_guard"]
        },
        "all_rounder": {
            "essential": ["bat", "batting_gloves", "pads", "helmet", "ball"],
            "recommended": ["thigh_guard", "abdominal_guard", "shoes", "kit_bag"],
            "optional": ["bat_grip", "arm_guard", "wrist_band"]
        }
    }
    
    def __init__(self, db: Database):
        self.db = db
    
    async def suggest_complementary_products(
        self,
        cart_items: List[int],
        session_id: str,
        max_suggestions: int = 3
    ) -> List[Dict]:
        """
        Suggest complementary products based on cart items.
        
        This implements "Complete Your Kit" logic by analyzing what's in the cart
        and suggesting items that complete the cricket kit.
        """
        if not cart_items:
            return []
        
        # Get categories of items in cart
        cart_query = """
        SELECT DISTINCT category, subcategory
        FROM products
        WHERE id = ANY($1)
        """
        
        try:
            cart_categories = await self.db.fetch_all(cart_query, cart_items)
            categories_in_cart = {row["category"] for row in cart_categories}
            
            # Determine complementary categories
            complementary_categories = set()
            for category in categories_in_cart:
                if category in self.CROSS_SELL_RULES:
                    complementary_categories.update(self.CROSS_SELL_RULES[category])
            
            # Remove categories already in cart
            complementary_categories -= categories_in_cart
            
            if not complementary_categories:
                return []
            
            # Get products from complementary categories
            suggestions_query = """
            SELECT id, name, price, rating, image_url, category, specifications
            FROM products
            WHERE category = ANY($1)
            AND in_stock = true
            AND id != ALL($2)
            ORDER BY rating DESC, sales_count DESC
            LIMIT $3
            """
            
            results = await self.db.fetch_all(
                suggestions_query,
                list(complementary_categories),
                cart_items,
                max_suggestions
            )
            
            suggestions = []
            for row in results:
                reason = self._get_cross_sell_reason(row["category"], categories_in_cart)
                suggestions.append({
                    "product_id": row["id"],
                    "name": row["name"],
                    "price": float(row["price"]),
                    "rating": float(row["rating"]),
                    "image_url": row["image_url"],
                    "category": row["category"],
                    "reason": reason,
                    "recommendation_type": "cross_sell"
                })
            
            # Track recommendations
            await self._track_recommendations(session_id, suggestions, "cross_sell")
            
            logger.info(
                "complementary_products_suggested",
                session_id=session_id,
                cart_items_count=len(cart_items),
                suggestions_count=len(suggestions)
            )
            
            return suggestions
            
        except Exception as e:
            logger.error("suggest_complementary_failed", error=str(e), session_id=session_id)
            return []
    
    def _get_cross_sell_reason(self, suggested_category: str, cart_categories: Set[str]) -> str:
        """Generate reason for cross-sell suggestion"""
        
        reasons = {
            "batting_gloves": "Essential protection to complete your batting gear",
            "bat_grip": "Improve your bat's grip and control",
            "scuff_sheet": "Protect your bat's face from damage",
            "knocking_oil": "Properly maintain your bat for longer life",
            "bat_cover": "Keep your bat safe during transport",
            "pads": "Complete leg protection for batting",
            "helmet": "Essential head protection for safety",
            "thigh_guard": "Additional protection for upper leg",
            "abdominal_guard": "Essential protection for all batsmen",
            "shoes": "Proper footwear for better performance",
            "kit_bag": "Carry all your gear conveniently",
            "ball": "Practice balls for training sessions"
        }
        
        return reasons.get(suggested_category, f"Complete your cricket kit with {suggested_category.replace('_', ' ')}")
    
    async def find_bundles(
        self,
        cart_items: List[int],
        session_id: str
    ) -> List[Dict]:
        """
        Find pre-configured bundles based on cart items.
        
        Example: User has bat + gloves → Suggest helmet for 10% off total
        """
        if not cart_items:
            return []
        
        query = """
        SELECT 
            pb.id,
            pb.bundle_id,
            pb.bundle_name,
            pb.primary_product_id,
            pb.complementary_product_ids,
            pb.discount_percentage,
            pb.bundle_description,
            p.name as primary_product_name,
            p.price as primary_product_price
        FROM product_bundles pb
        JOIN products p ON pb.primary_product_id = p.id
        WHERE pb.primary_product_id = ANY($1)
        AND pb.active = true
        ORDER BY pb.discount_percentage DESC, pb.display_order
        LIMIT 3
        """
        
        try:
            results = await self.db.fetch_all(query, cart_items)
            
            bundles = []
            for row in results:
                # Get complementary product details
                comp_products_query = """
                SELECT id, name, price, image_url
                FROM products
                WHERE id = ANY($1)
                AND in_stock = true
                """
                comp_products = await self.db.fetch_all(
                    comp_products_query,
                    row["complementary_product_ids"]
                )
                
                if not comp_products:
                    continue
                
                # Calculate bundle savings
                total_price = float(row["primary_product_price"])
                for comp in comp_products:
                    total_price += float(comp["price"])
                
                discount_amount = total_price * (float(row["discount_percentage"]) / 100)
                bundle_price = total_price - discount_amount
                
                bundles.append({
                    "bundle_id": row["bundle_id"],
                    "bundle_name": row["bundle_name"],
                    "description": row["bundle_description"],
                    "primary_product_id": row["primary_product_id"],
                    "complementary_products": [
                        {
                            "id": comp["id"],
                            "name": comp["name"],
                            "price": float(comp["price"]),
                            "image_url": comp["image_url"]
                        }
                        for comp in comp_products
                    ],
                    "original_price": total_price,
                    "bundle_price": bundle_price,
                    "savings": discount_amount,
                    "discount_percentage": float(row["discount_percentage"]),
                    "recommendation_type": "bundle"
                })
            
            logger.info(
                "bundles_found",
                session_id=session_id,
                bundles_count=len(bundles)
            )
            
            return bundles
            
        except Exception as e:
            logger.error("find_bundles_failed", error=str(e), session_id=session_id)
            return []
    
    async def suggest_upsell(
        self,
        product_id: int,
        session_id: str,
        max_suggestions: int = 2
    ) -> List[Dict]:
        """
        Suggest higher-value alternatives to a product.
        
        Example: User looking at NPR 3000 bat → Suggest NPR 5000 bat with better features
        """
        # Get the current product
        product_query = """
        SELECT id, name, price, category, subcategory, rating
        FROM products
        WHERE id = $1
        """
        
        try:
            product = await self.db.fetch_one(product_query, product_id)
            
            if not product:
                return []
            
            current_price = float(product["price"])
            
            # Find higher-priced products in same category (20-50% more expensive)
            upsell_query = """
            SELECT id, name, price, rating, image_url, specifications
            FROM products
            WHERE category = $1
            AND price > $2
            AND price <= $3
            AND in_stock = true
            AND id != $4
            ORDER BY rating DESC, sales_count DESC
            LIMIT $5
            """
            
            min_upsell_price = current_price * 1.2  # 20% more
            max_upsell_price = current_price * 1.5  # 50% more
            
            results = await self.db.fetch_all(
                upsell_query,
                product["category"],
                min_upsell_price,
                max_upsell_price,
                product_id,
                max_suggestions
            )
            
            upsells = []
            for row in results:
                price_diff = float(row["price"]) - current_price
                reason = self._get_upsell_reason(
                    product["category"],
                    price_diff,
                    float(row["rating"]),
                    float(product["rating"])
                )
                
                upsells.append({
                    "product_id": row["id"],
                    "name": row["name"],
                    "price": float(row["price"]),
                    "rating": float(row["rating"]),
                    "image_url": row["image_url"],
                    "price_difference": price_diff,
                    "reason": reason,
                    "recommendation_type": "upsell"
                })
            
            # Track recommendations
            await self._track_recommendations(session_id, upsells, "upsell")
            
            logger.info(
                "upsell_suggested",
                session_id=session_id,
                product_id=product_id,
                upsells_count=len(upsells)
            )
            
            return upsells
            
        except Exception as e:
            logger.error("suggest_upsell_failed", error=str(e), product_id=product_id)
            return []
    
    def _get_upsell_reason(
        self,
        category: str,
        price_diff: float,
        upsell_rating: float,
        current_rating: float
    ) -> str:
        """Generate reason for upsell suggestion"""
        
        reasons = []
        
        if upsell_rating > current_rating:
            rating_diff = upsell_rating - current_rating
            reasons.append(f"Higher rated ({rating_diff:.1f}★ better)")
        
        if category == "bat":
            reasons.append("Better willow grade for improved performance")
        elif category in ["batting_gloves", "gloves"]:
            reasons.append("Premium materials for better protection")
        elif category == "pads":
            reasons.append("Enhanced protection and comfort")
        
        reasons.append(f"Just NPR {price_diff:.0f} more")
        
        return " • ".join(reasons)
    
    async def get_complete_kit_suggestions(
        self,
        cart_items: List[int],
        user_position: Optional[str],
        session_id: str
    ) -> Dict:
        """
        Analyze cart and suggest items to complete a cricket kit.
        
        Returns categorized suggestions: essential, recommended, optional
        """
        if not cart_items:
            return {"essential": [], "recommended": [], "optional": []}
        
        # Get categories in cart
        cart_query = """
        SELECT DISTINCT category
        FROM products
        WHERE id = ANY($1)
        """
        
        try:
            cart_categories = await self.db.fetch_all(cart_query, cart_items)
            categories_in_cart = {row["category"] for row in cart_categories}
            
            # Determine player position if not provided
            if not user_position:
                if "bat" in categories_in_cart or "batting_gloves" in categories_in_cart:
                    user_position = "batsman"
                elif "wicket_keeping_gloves" in categories_in_cart:
                    user_position = "wicket_keeper"
                else:
                    user_position = "all_rounder"
            
            # Get kit template
            kit_template = self.COMPLETE_KIT_TEMPLATES.get(user_position, self.COMPLETE_KIT_TEMPLATES["batsman"])
            
            # Find missing items
            result = {
                "essential": [],
                "recommended": [],
                "optional": []
            }
            
            for priority in ["essential", "recommended", "optional"]:
                missing_categories = set(kit_template[priority]) - categories_in_cart
                
                if missing_categories:
                    # Get products from missing categories
                    products_query = """
                    SELECT id, name, price, rating, image_url, category
                    FROM products
                    WHERE category = ANY($1)
                    AND in_stock = true
                    ORDER BY rating DESC, sales_count DESC
                    LIMIT 2
                    """
                    
                    products = await self.db.fetch_all(
                        products_query,
                        list(missing_categories)
                    )
                    
                    for product in products:
                        result[priority].append({
                            "product_id": product["id"],
                            "name": product["name"],
                            "price": float(product["price"]),
                            "rating": float(product["rating"]),
                            "image_url": product["image_url"],
                            "category": product["category"],
                            "priority": priority
                        })
            
            logger.info(
                "complete_kit_suggested",
                session_id=session_id,
                user_position=user_position,
                essential_count=len(result["essential"]),
                recommended_count=len(result["recommended"])
            )
            
            return result
            
        except Exception as e:
            logger.error("get_complete_kit_failed", error=str(e), session_id=session_id)
            return {"essential": [], "recommended": [], "optional": []}
    
    async def _track_recommendations(
        self,
        session_id: str,
        recommendations: List[Dict],
        recommendation_type: str
    ):
        """Track recommendations in database for analytics"""
        
        try:
            for idx, rec in enumerate(recommendations):
                query = """
                INSERT INTO product_recommendations (
                    session_id, product_id, recommendation_type, reason, position, context
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                """
                
                await self.db.execute(
                    query,
                    session_id,
                    rec.get("product_id"),
                    recommendation_type,
                    rec.get("reason", ""),
                    idx + 1,
                    {"price": rec.get("price"), "rating": rec.get("rating")}
                )
        except Exception as e:
            logger.error("track_recommendations_failed", error=str(e))
    
    async def mark_recommendation_accepted(
        self,
        session_id: str,
        product_id: int
    ):
        """Mark a recommendation as accepted (user added to cart or purchased)"""
        
        try:
            query = """
            UPDATE product_recommendations
            SET accepted = true
            WHERE session_id = $1
            AND product_id = $2
            AND accepted = false
            """
            
            await self.db.execute(query, session_id, product_id)
            
            logger.info(
                "recommendation_accepted",
                session_id=session_id,
                product_id=product_id
            )
        except Exception as e:
            logger.error("mark_recommendation_accepted_failed", error=str(e))
    
    async def get_frequently_bought_together(
        self,
        product_id: int,
        limit: int = 3
    ) -> List[Dict]:
        """
        Find products frequently bought together with the given product.
        
        Uses order history to find common product combinations.
        """
        query = """
        WITH product_orders AS (
            SELECT DISTINCT oi.order_id
            FROM order_items oi
            WHERE oi.product_id = $1
        ),
        co_purchased AS (
            SELECT 
                oi.product_id,
                p.name,
                p.price,
                p.image_url,
                p.category,
                COUNT(*) as purchase_count
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id IN (SELECT order_id FROM product_orders)
            AND oi.product_id != $1
            AND p.in_stock = true
            GROUP BY oi.product_id, p.name, p.price, p.image_url, p.category
            ORDER BY purchase_count DESC
            LIMIT $2
        )
        SELECT product_id, name, price, image_url, category, purchase_count
        FROM co_purchased
        """
        
        try:
            results = await self.db.fetch_all(query, product_id, limit)
            
            return [{
                "product_id": row["product_id"],
                "name": row["name"],
                "price": float(row["price"]),
                "image_url": row["image_url"],
                "category": row["category"],
                "purchase_count": row["purchase_count"],
                "reason": f"Frequently bought together ({row['purchase_count']} times)"
            } for row in results]
            
        except Exception as e:
            logger.error("get_frequently_bought_together_failed", error=str(e))
            return []


def get_recommendation_engine() -> RecommendationEngine:
    """Dependency injection for RecommendationEngine"""
    from app.db.database import db
    return RecommendationEngine(db)

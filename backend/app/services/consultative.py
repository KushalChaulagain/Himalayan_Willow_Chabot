"""
Consultative Service for Cricket Equipment Recommendations

This service implements consultative selling patterns with cricket expertise,
need-based filtering, and progressive disclosure question sequencing.
"""

import re
from typing import Dict, List, Optional, Tuple
import structlog
from fastapi import Depends
from app.db.database import Database, get_db
from app.models.product import Product

logger = structlog.get_logger()


class ConsultativeService:
    """Service for consultative selling with cricket expertise"""
    
    # Cricket expertise knowledge base
    CRICKET_KNOWLEDGE = {
        "bat_types": {
            "english_willow": {
                "description": "Premium wood used by professionals",
                "price_range": (8000, 50000),
                "best_for": ["professional", "club"],
                "characteristics": "Lighter weight, better performance, larger sweet spot",
                "playing_surface": ["turf", "leather_ball"]
            },
            "kashmir_willow": {
                "description": "Budget-friendly option for practice and club cricket",
                "price_range": (2000, 8000),
                "best_for": ["beginner", "club"],
                "characteristics": "Heavier, durable, good for learning",
                "playing_surface": ["cement", "turf", "tape_ball"]
            },
            "tape_ball": {
                "description": "Lightweight bats for tape ball cricket",
                "price_range": (1500, 4000),
                "best_for": ["beginner", "recreational"],
                "characteristics": "Very light, designed for tape ball",
                "playing_surface": ["cement", "street"]
            }
        },
        "playing_surfaces": {
            "turf": {
                "recommended_equipment": {
                    "bat": "english_willow",
                    "shoes": "spiked_cricket_shoes",
                    "ball": "leather_ball"
                },
                "characteristics": "Natural grass, requires proper cricket gear"
            },
            "cement": {
                "recommended_equipment": {
                    "bat": "kashmir_willow",
                    "shoes": "rubber_sole_shoes",
                    "ball": "tennis_ball_or_leather"
                },
                "characteristics": "Hard surface, more wear on equipment"
            },
            "matting": {
                "recommended_equipment": {
                    "bat": "kashmir_willow_or_english",
                    "shoes": "rubber_sole_shoes",
                    "ball": "leather_ball"
                },
                "characteristics": "Artificial surface, moderate bounce"
            }
        },
        "player_levels": {
            "beginner": {
                "budget_suggestion": (2000, 5000),
                "bat_weight": "1000-1100g",
                "bat_type": "kashmir_willow",
                "focus": "Learning basics, durability over performance"
            },
            "club": {
                "budget_suggestion": (4000, 12000),
                "bat_weight": "1100-1200g",
                "bat_type": "kashmir_willow_grade_a_or_english_willow_grade_3",
                "focus": "Balance of performance and value"
            },
            "professional": {
                "budget_suggestion": (10000, 50000),
                "bat_weight": "1150-1200g",
                "bat_type": "english_willow_grade_1_2",
                "focus": "Maximum performance, professional quality"
            }
        }
    }
    
    # Cross-sell rules based on primary product category
    CROSS_SELL_RULES = {
        "bat": ["batting_gloves", "bat_grip", "scuff_sheet", "knocking_oil", "bat_cover"],
        "batting_gloves": ["bat", "pads", "helmet", "thigh_guard"],
        "pads": ["batting_gloves", "helmet", "thigh_guard", "abdominal_guard"],
        "helmet": ["batting_gloves", "pads", "thigh_guard"],
        "ball": ["ball_box", "practice_stumps", "bowling_machine"],
        "shoes": ["socks", "shoe_bag"],
        "kit_bag": ["bat_cover", "shoe_bag", "water_bottle"]
    }
    
    def __init__(self, db: Database):
        self.db = db
    
    async def gather_user_context(
        self, 
        session_id: str, 
        user_message: str,
        existing_context: Optional[Dict] = None
    ) -> Dict:
        """
        Extract cricket-specific context from conversation.
        
        Detects:
        - Playing level (beginner/club/professional)
        - Surface preference (turf/cement/matting)
        - Budget range
        - Position (batsman/bowler/all-rounder/wicket-keeper)
        - Age group
        """
        context = existing_context or {}
        message_lower = user_message.lower()
        
        # Detect playing level
        if not context.get("playing_level"):
            if any(word in message_lower for word in ["beginner", "starting", "first time", "new to cricket", "learning"]):
                context["playing_level"] = "beginner"
            elif any(word in message_lower for word in ["club", "team", "league", "tournament", "intermediate"]):
                context["playing_level"] = "club"
            elif any(word in message_lower for word in ["professional", "pro", "serious", "competitive", "advanced"]):
                context["playing_level"] = "professional"
        
        # Detect surface preference
        if not context.get("preferred_surface"):
            if "turf" in message_lower or "grass" in message_lower:
                context["preferred_surface"] = "turf"
            elif "cement" in message_lower or "concrete" in message_lower:
                context["preferred_surface"] = "cement"
            elif "matting" in message_lower or "mat" in message_lower:
                context["preferred_surface"] = "matting"
            elif "tape ball" in message_lower:
                context["preferred_surface"] = "street"
        
        # Detect budget
        if not context.get("budget_range"):
            budget_match = re.search(r'(\d+)\s*(?:k|thousand|rupees|rs|npr)', message_lower)
            if budget_match:
                budget = int(budget_match.group(1))
                if "k" in message_lower or "thousand" in message_lower:
                    budget = budget * 1000 if budget < 100 else budget
                
                if budget < 3000:
                    context["budget_range"] = "under_3k"
                elif budget < 7000:
                    context["budget_range"] = "3k_7k"
                elif budget < 15000:
                    context["budget_range"] = "7k_15k"
                else:
                    context["budget_range"] = "no_limit"
        
        # Detect position
        if not context.get("position"):
            if any(word in message_lower for word in ["batsman", "batting", "bat"]):
                context["position"] = "batsman"
            elif any(word in message_lower for word in ["bowler", "bowling", "bowl"]):
                context["position"] = "bowler"
            elif any(word in message_lower for word in ["all rounder", "all-rounder", "both bat and bowl"]):
                context["position"] = "all_rounder"
            elif any(word in message_lower for word in ["wicket keeper", "keeper", "wk"]):
                context["position"] = "wicket_keeper"
        
        # Detect age group
        if not context.get("age_group"):
            age_match = re.search(r'(\d+)\s*(?:year|yr)', message_lower)
            if age_match:
                age = int(age_match.group(1))
                if age < 16:
                    context["age_group"] = "youth"
                elif age < 40:
                    context["age_group"] = "adult"
                else:
                    context["age_group"] = "senior"
            elif any(word in message_lower for word in ["kid", "child", "junior", "youth"]):
                context["age_group"] = "youth"
        
        # Save context to database
        await self._save_user_context(session_id, context)
        
        logger.info(
            "user_context_gathered",
            session_id=session_id,
            context=context
        )
        
        return context
    
    async def _save_user_context(self, session_id: str, context: Dict):
        """Save user context to user_profiles table"""
        try:
            # Check if profile exists
            check_query = "SELECT id FROM user_profiles WHERE session_id = $1"
            existing = await self.db.fetch_one(check_query, session_id)
            
            if existing:
                # Update existing profile
                update_query = """
                UPDATE user_profiles
                SET playing_level = COALESCE($2, playing_level),
                    preferred_surface = COALESCE($3, preferred_surface),
                    budget_range = COALESCE($4, budget_range),
                    position = COALESCE($5, position),
                    age_group = COALESCE($6, age_group),
                    insights = $7,
                    updated_at = NOW()
                WHERE session_id = $1
                """
                await self.db.execute(
                    update_query,
                    session_id,
                    context.get("playing_level"),
                    context.get("preferred_surface"),
                    context.get("budget_range"),
                    context.get("position"),
                    context.get("age_group"),
                    context
                )
            else:
                # Insert new profile
                insert_query = """
                INSERT INTO user_profiles (
                    session_id, playing_level, preferred_surface, budget_range,
                    position, age_group, insights
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """
                await self.db.execute(
                    insert_query,
                    session_id,
                    context.get("playing_level"),
                    context.get("preferred_surface"),
                    context.get("budget_range"),
                    context.get("position"),
                    context.get("age_group"),
                    context
                )
        except Exception as e:
            logger.error("save_user_context_failed", error=str(e), session_id=session_id)
    
    async def get_next_question(self, context: Dict) -> Optional[Tuple[str, List[str]]]:
        """
        Progressive disclosure: determine next question to ask.
        
        Returns: (question_text, quick_reply_options) or None if enough context
        """
        # Question sequence priority
        if not context.get("playing_level"):
            return (
                "What's your playing level? This helps me recommend the right equipment for you.",
                ["Beginner", "Club/Intermediate", "Professional"]
            )
        
        if not context.get("budget_range"):
            return (
                "What's your budget range for this purchase?",
                ["Under NPR 3,000", "NPR 3,000-7,000", "NPR 7,000-15,000", "No limit"]
            )
        
        if not context.get("preferred_surface"):
            return (
                "What type of surface do you usually play on? This affects the equipment choice.",
                ["Turf (grass)", "Cement/Concrete", "Matting", "Mixed/All surfaces"]
            )
        
        # Enough context gathered
        return None
    
    async def recommend_with_reasoning(
        self, 
        user_context: Dict,
        category: str,
        max_price: Optional[float] = None
    ) -> List[Dict]:
        """
        Generate product recommendations with outcome-driven explanations.
        
        Returns list of recommendations with reasoning based on user context.
        """
        playing_level = user_context.get("playing_level", "beginner")
        surface = user_context.get("preferred_surface", "cement")
        budget_range = user_context.get("budget_range", "under_3k")
        
        # Determine price range from budget
        price_ranges = {
            "under_3k": (0, 3000),
            "3k_7k": (3000, 7000),
            "7k_15k": (7000, 15000),
            "no_limit": (0, 100000)
        }
        min_price, max_price_from_budget = price_ranges.get(budget_range, (0, 100000))
        
        if max_price:
            max_price_from_budget = min(max_price, max_price_from_budget)
        
        # Get recommendations from knowledge base
        recommendations = []
        
        if category == "bat":
            recommendations = await self._recommend_bat(
                playing_level, surface, min_price, max_price_from_budget
            )
        elif category in ["batting_gloves", "gloves"]:
            recommendations = await self._recommend_gloves(
                playing_level, min_price, max_price_from_budget
            )
        elif category == "pads":
            recommendations = await self._recommend_pads(
                playing_level, min_price, max_price_from_budget
            )
        else:
            # Generic recommendation
            recommendations = await self._recommend_generic(
                category, min_price, max_price_from_budget
            )
        
        logger.info(
            "consultative_recommendations_generated",
            category=category,
            playing_level=playing_level,
            recommendations_count=len(recommendations)
        )
        
        return recommendations
    
    async def _recommend_bat(
        self, 
        playing_level: str, 
        surface: str,
        min_price: float,
        max_price: float
    ) -> List[Dict]:
        """Recommend bats with cricket-specific reasoning"""
        
        # Determine bat type based on level and surface
        knowledge = self.CRICKET_KNOWLEDGE["player_levels"].get(playing_level, {})
        
        # Build reasoning
        reasons = []
        
        if playing_level == "beginner":
            reasons.append("Perfect for learning the basics")
            reasons.append("Durable Kashmir Willow construction")
        elif playing_level == "club":
            reasons.append("Great balance of performance and value")
            reasons.append("Suitable for competitive club cricket")
        else:  # professional
            reasons.append("Professional-grade English Willow")
            reasons.append("Maximum performance and sweet spot")
        
        if surface == "turf":
            reasons.append("Ideal for turf wickets and leather ball")
        elif surface == "cement":
            reasons.append("Built to handle hard cement surfaces")
        
        # Query products
        query = """
        SELECT id, name, price, rating, image_url, specifications, description
        FROM products
        WHERE category = 'bat'
        AND price BETWEEN $1 AND $2
        AND in_stock = true
        ORDER BY rating DESC, sales_count DESC
        LIMIT 3
        """
        
        try:
            results = await self.db.fetch_all(query, min_price, max_price)
            
            recommendations = []
            for idx, row in enumerate(results):
                reason = reasons[idx % len(reasons)] if reasons else "Highly rated bat"
                recommendations.append({
                    "product_id": row["id"],
                    "name": row["name"],
                    "price": float(row["price"]),
                    "rating": float(row["rating"]),
                    "image_url": row["image_url"],
                    "reason": reason,
                    "specifications": row["specifications"]
                })
            
            return recommendations
        except Exception as e:
            logger.error("recommend_bat_failed", error=str(e))
            return []
    
    async def _recommend_gloves(
        self,
        playing_level: str,
        min_price: float,
        max_price: float
    ) -> List[Dict]:
        """Recommend batting gloves with reasoning"""
        
        reasons = {
            "beginner": "Good protection for learning proper technique",
            "club": "Professional-grade protection for competitive play",
            "professional": "Maximum protection and comfort for serious players"
        }
        
        reason = reasons.get(playing_level, "Quality batting gloves")
        
        query = """
        SELECT id, name, price, rating, image_url, specifications
        FROM products
        WHERE category IN ('batting_gloves', 'gloves')
        AND price BETWEEN $1 AND $2
        AND in_stock = true
        ORDER BY rating DESC, sales_count DESC
        LIMIT 3
        """
        
        try:
            results = await self.db.fetch_all(query, min_price, max_price)
            
            return [{
                "product_id": row["id"],
                "name": row["name"],
                "price": float(row["price"]),
                "rating": float(row["rating"]),
                "image_url": row["image_url"],
                "reason": reason,
                "specifications": row["specifications"]
            } for row in results]
        except Exception as e:
            logger.error("recommend_gloves_failed", error=str(e))
            return []
    
    async def _recommend_pads(
        self,
        playing_level: str,
        min_price: float,
        max_price: float
    ) -> List[Dict]:
        """Recommend pads with reasoning"""
        
        reasons = {
            "beginner": "Lightweight protection perfect for beginners",
            "club": "Professional protection for club-level cricket",
            "professional": "Maximum protection for fast bowling"
        }
        
        reason = reasons.get(playing_level, "Quality leg protection")
        
        query = """
        SELECT id, name, price, rating, image_url, specifications
        FROM products
        WHERE category = 'pads'
        AND price BETWEEN $1 AND $2
        AND in_stock = true
        ORDER BY rating DESC, sales_count DESC
        LIMIT 3
        """
        
        try:
            results = await self.db.fetch_all(query, min_price, max_price)
            
            return [{
                "product_id": row["id"],
                "name": row["name"],
                "price": float(row["price"]),
                "rating": float(row["rating"]),
                "image_url": row["image_url"],
                "reason": reason,
                "specifications": row["specifications"]
            } for row in results]
        except Exception as e:
            logger.error("recommend_pads_failed", error=str(e))
            return []
    
    async def _recommend_generic(
        self,
        category: str,
        min_price: float,
        max_price: float
    ) -> List[Dict]:
        """Generic product recommendation"""
        
        query = """
        SELECT id, name, price, rating, image_url, specifications
        FROM products
        WHERE category = $1
        AND price BETWEEN $2 AND $3
        AND in_stock = true
        ORDER BY rating DESC, sales_count DESC
        LIMIT 3
        """
        
        try:
            results = await self.db.fetch_all(query, category, min_price, max_price)
            
            return [{
                "product_id": row["id"],
                "name": row["name"],
                "price": float(row["price"]),
                "rating": float(row["rating"]),
                "image_url": row["image_url"],
                "reason": f"Highly rated {category.replace('_', ' ')}",
                "specifications": row["specifications"]
            } for row in results]
        except Exception as e:
            logger.error("recommend_generic_failed", error=str(e), category=category)
            return []
    
    def get_cricket_advice(self, category: str, context: Dict) -> str:
        """Get cricket-specific advice based on context"""
        
        playing_level = context.get("playing_level", "beginner")
        surface = context.get("preferred_surface")
        
        advice = []
        
        if category == "bat":
            if playing_level == "beginner":
                advice.append("💡 Tip: Start with a Kashmir Willow bat - it's more durable while you're learning.")
            elif playing_level == "professional" and surface == "turf":
                advice.append("💡 Tip: English Willow performs best on turf wickets with leather balls.")
            
            advice.append("🏏 Remember to knock in your bat properly before first use!")
        
        elif category in ["batting_gloves", "gloves"]:
            advice.append("💡 Tip: Make sure gloves fit snugly - too loose affects grip and control.")
        
        elif category == "pads":
            advice.append("💡 Tip: Pads should cover from knee to ankle for proper protection.")
        
        return " ".join(advice) if advice else ""


def get_consultative_service() -> ConsultativeService:
    """Dependency injection for ConsultativeService"""
    from app.db.database import db
    return ConsultativeService(db)

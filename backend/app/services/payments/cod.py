import httpx
import structlog
from typing import Dict
from datetime import datetime

from app.config import settings

logger = structlog.get_logger()


class CODService:
    """Cash on Delivery service"""
    
    COD_LIMIT = 50000  # Maximum NPR 50,000 for COD
    
    async def create_cod_order(
        self,
        order_id: str,
        total_amount: float,
        delivery_address: Dict,
        customer_phone: str
    ) -> Dict:
        """Create COD order with validation"""
        
        # Validate delivery address
        required_fields = ["street", "city", "postal_code"]
        if not all(field in delivery_address for field in required_fields):
            return {
                "success": False,
                "error": "Incomplete delivery address"
            }
        
        # COD limit check
        if total_amount > self.COD_LIMIT:
            return {
                "success": False,
                "error": f"COD not available for orders above NPR {self.COD_LIMIT:,.0f}"
            }
        
        # Send notification to store team
        await self._notify_store_team(
            order_id,
            total_amount,
            customer_phone,
            delivery_address
        )
        
        logger.info(
            "cod_order_created",
            order_id=order_id,
            amount=total_amount
        )
        
        return {
            "success": True,
            "order_id": order_id,
            "payment_method": "COD",
            "message": "Order confirmed! Our team will call you before dispatch."
        }
    
    async def _notify_store_team(
        self,
        order_id: str,
        amount: float,
        phone: str,
        address: Dict
    ):
        """Send Telegram notification to store team"""
        
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            logger.warning("telegram_not_configured")
            return
        
        message = f"""
🆕 New COD Order

Order ID: {order_id}
Amount: NPR {amount:,.2f}
Phone: {phone}
Address: {address.get('street')}, {address.get('city')} - {address.get('postal_code')}

Action Required: Call customer to confirm order
"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                    json={
                        "chat_id": settings.telegram_chat_id,
                        "text": message,
                        "parse_mode": "HTML"
                    },
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    logger.info("telegram_notification_sent", order_id=order_id)
                else:
                    logger.error(
                        "telegram_notification_failed",
                        status_code=response.status_code
                    )
                    
        except Exception as e:
            logger.error("telegram_notification_error", error=str(e))


# Global COD service instance
cod_service = CODService()


def get_cod_service() -> CODService:
    """Dependency to get COD service"""
    return cod_service

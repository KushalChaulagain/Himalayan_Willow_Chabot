import httpx
import structlog
from typing import Dict, Optional

from app.config import settings

logger = structlog.get_logger()


class KhaltiService:
    """Khalti payment gateway integration"""
    
    def __init__(self):
        self.secret_key = settings.khalti_secret_key
        self.base_url = settings.khalti_base_url
    
    async def initiate_payment(
        self,
        order_id: str,
        amount: int,  # Amount in paisa (1 NPR = 100 paisa)
        product_name: str,
        customer_info: Dict,
        return_url: str,
        website_url: str
    ) -> Dict:
        """Initiate Khalti payment"""
        
        # Amount must be in paisa
        if amount < 1000:  # Minimum NPR 10
            raise ValueError("Amount too low for Khalti payment")
        
        payload = {
            "return_url": return_url,
            "website_url": website_url,
            "amount": amount,
            "purchase_order_id": order_id,
            "purchase_order_name": product_name,
            "customer_info": {
                "name": customer_info.get("name"),
                "email": customer_info.get("email"),
                "phone": customer_info.get("phone")
            }
        }
        
        headers = {
            "Authorization": f"Key {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v2/epayment/initiate/",
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(
                        "khalti_payment_initiated",
                        order_id=order_id,
                        pidx=data.get("pidx")
                    )
                    return {
                        "success": True,
                        "payment_url": data.get("payment_url"),
                        "pidx": data.get("pidx"),
                        "expires_at": data.get("expires_at")
                    }
                else:
                    logger.error(
                        "khalti_initiation_failed",
                        order_id=order_id,
                        status_code=response.status_code,
                        response=response.text
                    )
                    return {
                        "success": False,
                        "error": "Failed to initiate Khalti payment"
                    }
                    
        except httpx.TimeoutException:
            logger.error("khalti_initiation_timeout", order_id=order_id)
            return {
                "success": False,
                "error": "Khalti payment gateway timeout"
            }
        except Exception as e:
            logger.error("khalti_initiation_error", error=str(e), order_id=order_id)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def verify_payment(self, pidx: str) -> Optional[Dict]:
        """Verify Khalti payment status"""
        
        headers = {
            "Authorization": f"Key {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        payload = {"pidx": pidx}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v2/epayment/lookup/",
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "Completed":
                        logger.info(
                            "khalti_payment_verified",
                            pidx=pidx,
                            transaction_id=data.get("transaction_id")
                        )
                        return {
                            "success": True,
                            "transaction_id": data.get("transaction_id"),
                            "amount": data.get("total_amount"),
                            "status": data.get("status")
                        }
                    else:
                        logger.warning(
                            "khalti_payment_incomplete",
                            pidx=pidx,
                            status=data.get("status")
                        )
                        return {
                            "success": False,
                            "status": data.get("status")
                        }
                else:
                    logger.error(
                        "khalti_verification_failed",
                        pidx=pidx,
                        status_code=response.status_code
                    )
                    return None
                    
        except httpx.TimeoutException:
            logger.error("khalti_verification_timeout", pidx=pidx)
            return None
        except Exception as e:
            logger.error("khalti_verification_error", error=str(e), pidx=pidx)
            return None


# Global Khalti service instance
khalti_service = KhaltiService()


def get_khalti_service() -> KhaltiService:
    """Dependency to get Khalti service"""
    return khalti_service

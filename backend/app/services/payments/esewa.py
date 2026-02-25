import hmac
import hashlib
import httpx
import structlog
from typing import Dict, Optional
from datetime import datetime

from app.config import settings

logger = structlog.get_logger()


class ESewaService:
    """eSewa payment gateway integration"""
    
    def __init__(self):
        self.merchant_id = settings.esewa_merchant_id
        self.secret_key = settings.esewa_secret_key
        self.base_url = settings.esewa_base_url
    
    def generate_payment(
        self,
        order_id: str,
        amount: float,
        success_url: str,
        failure_url: str
    ) -> Dict:
        """Generate signed eSewa payment request"""
        
        if amount <= 0:
            raise ValueError("Invalid payment amount")
        
        # Create signature
        message = f"total_amount={amount},transaction_uuid={order_id},product_code={self.merchant_id}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        payment_data = {
            "amount": amount,
            "tax_amount": 0,
            "total_amount": amount,
            "transaction_uuid": order_id,
            "product_code": self.merchant_id,
            "product_service_charge": 0,
            "product_delivery_charge": 0,
            "success_url": success_url,
            "failure_url": failure_url,
            "signed_field_names": "total_amount,transaction_uuid,product_code",
            "signature": signature
        }
        
        logger.info(
            "esewa_payment_initiated",
            order_id=order_id,
            amount=amount,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return {
            "payment_url": f"{self.base_url}/epay/main",
            "payment_data": payment_data
        }
    
    async def verify_payment(
        self,
        order_id: str,
        amount: float,
        ref_id: str
    ) -> bool:
        """Verify payment with eSewa verification API"""
        
        verification_url = f"{self.base_url}/api/epay/transaction/status/"
        
        params = {
            "product_code": self.merchant_id,
            "total_amount": amount,
            "transaction_uuid": order_id
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    verification_url,
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(
                        "esewa_verification_failed",
                        order_id=order_id,
                        status_code=response.status_code
                    )
                    return False
                
                data = response.json()
                
                # Verify transaction status
                if data.get("status") == "COMPLETE" and data.get("refId") == ref_id:
                    logger.info(
                        "esewa_payment_verified",
                        order_id=order_id,
                        ref_id=ref_id
                    )
                    return True
                
                logger.warning(
                    "esewa_payment_verification_mismatch",
                    order_id=order_id,
                    expected_ref=ref_id,
                    actual_status=data.get("status")
                )
                return False
                
        except httpx.TimeoutException:
            logger.error("esewa_verification_timeout", order_id=order_id)
            return False
        except Exception as e:
            logger.error("esewa_verification_error", error=str(e), order_id=order_id)
            return False
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """Verify webhook signature from eSewa"""
        
        expected_signature = hmac.new(
            self.secret_key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)


# Global eSewa service instance
esewa_service = ESewaService()


def get_esewa_service() -> ESewaService:
    """Dependency to get eSewa service"""
    return esewa_service

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
import structlog

from app.models.payment import PaymentInitiateRequest, PaymentVerifyRequest
from app.services.payments.esewa import ESewaService, get_esewa_service
from app.services.payments.khalti import KhaltiService, get_khalti_service
from app.services.payments.cod import CODService, get_cod_service
from app.services.orders import OrderService
from app.db.database import Database, get_db
from app.config import settings
from app.limiter import limiter
from app.routes.auth import get_current_user_optional

logger = structlog.get_logger()


def _can_access_order(order, current_user: Optional[dict], session_id_header: Optional[str]) -> bool:
    """Check if requester is authorized to access the order."""
    if current_user and order.user_id and order.user_id == current_user["id"]:
        return True
    if session_id_header and order.session_id and order.session_id == session_id_header.strip():
        return True
    return False
router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/initiate")
@limiter.limit("60/minute")
async def initiate_payment(
    request: Request,
    body: PaymentInitiateRequest,
    esewa: ESewaService = Depends(get_esewa_service),
    khalti: KhaltiService = Depends(get_khalti_service),
    cod: CODService = Depends(get_cod_service)
):
    """Initiate payment based on method"""
    
    try:
        if body.payment_method.value == "esewa":
            result = esewa.generate_payment(
                order_id=body.order_id,
                amount=body.amount / 100,  # Convert paisa to NPR
                success_url=f"{settings.base_url}/api/payments/esewa/success",
                failure_url=f"{settings.base_url}/api/payments/esewa/failure"
            )
            return {
                "success": True,
                "payment_url": result["payment_url"],
                "payment_data": result["payment_data"]
            }
        
        elif body.payment_method.value == "khalti":
            result = await khalti.initiate_payment(
                order_id=body.order_id,
                amount=body.amount,  # Already in paisa
                product_name=f"Order {body.order_id}",
                customer_info=body.customer_info,
                return_url=f"{settings.base_url}/api/payments/khalti/callback",
                website_url=settings.base_url
            )
            return result
        
        elif body.payment_method.value == "cod":
            result = await cod.create_cod_order(
                order_id=body.order_id,
                total_amount=body.amount / 100,  # Convert to NPR
                delivery_address=body.customer_info.get("address", {}),
                customer_phone=body.customer_info.get("phone", "")
            )
            return result
        
        else:
            raise HTTPException(status_code=400, detail="Invalid payment method")
            
    except Exception as e:
        logger.error("payment_initiation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Payment initiation failed")


@router.post("/verify")
@limiter.limit("60/minute")
async def verify_payment(
    request: Request,
    body: PaymentVerifyRequest,
    esewa: ESewaService = Depends(get_esewa_service),
    khalti: KhaltiService = Depends(get_khalti_service),
    db: Database = Depends(get_db)
):
    """Verify payment completion"""
    
    order_service = OrderService(db)
    
    try:
        if body.payment_method.value == "esewa":
            # Get order to verify amount
            order = await order_service.get_order_by_id(body.order_id)
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            is_valid = await esewa.verify_payment(
                order_id=body.order_id,
                amount=order.total_amount / 100,
                ref_id=body.payment_reference
            )
            
            if is_valid:
                await order_service.mark_order_as_paid(
                    body.order_id,
                    body.payment_reference
                )
                return {"success": True, "message": "Payment verified"}
            else:
                return {"success": False, "message": "Payment verification failed"}
        
        elif body.payment_method.value == "khalti":
            result = await khalti.verify_payment(body.payment_reference)
            
            if result and result.get("success"):
                await order_service.mark_order_as_paid(
                    body.order_id,
                    result.get("transaction_id", body.payment_reference)
                )
                return {"success": True, "message": "Payment verified"}
            else:
                return {"success": False, "message": "Payment verification failed"}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid payment method")
            
    except Exception as e:
        logger.error("payment_verification_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Payment verification failed")


@router.post("/webhooks/esewa")
@limiter.limit("120/minute")
async def esewa_webhook(
    request: Request,
    esewa: ESewaService = Depends(get_esewa_service),
    db: Database = Depends(get_db)
):
    """eSewa webhook handler"""
    
    # Verify signature
    signature = request.headers.get("X-eSewa-Signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    
    body = await request.body()
    if not esewa.verify_webhook_signature(body, signature):
        logger.warning("esewa_webhook_invalid_signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process webhook (body already read for signature verification; parse from bytes)
    data = json.loads(body)
    order_id = data.get("transaction_uuid")
    ref_id = data.get("refId")
    
    # Verify payment
    order_service = OrderService(db)
    order = await order_service.get_order_by_id(order_id)
    
    if order:
        is_valid = await esewa.verify_payment(
            order_id,
            order.total_amount / 100,
            ref_id
        )
        
        if is_valid:
            await order_service.mark_order_as_paid(order_id, ref_id)
            return {"status": "success"}
    
    return {"status": "verification_failed"}


@router.get("/status/{order_id}")
@limiter.limit("60/minute")
async def get_payment_status(
    request: Request,
    order_id: str,
    db: Database = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
):
    """Get payment status for an order. Requires X-Session-ID or authenticated user matching order."""
    order_service = OrderService(db)
    order = await order_service.get_order_by_id(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not _can_access_order(order, current_user, x_session_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this order")
    
    return {
        "success": True,
        "order_id": order.order_id,
        "payment_status": order.payment_status.value,
        "payment_method": order.payment_method.value,
        "payment_reference": order.payment_reference
    }

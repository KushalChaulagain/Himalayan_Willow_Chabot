from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
import structlog

from app.models.order import OrderCreate, OrderTrackRequest
from app.limiter import limiter
from app.services.orders import OrderService
from app.db.database import Database, get_db
from app.routes.auth import get_current_user_optional

logger = structlog.get_logger()
router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("/create")
@limiter.limit("60/minute")
async def create_order(
    request: Request,
    order_data: OrderCreate,
    db: Database = Depends(get_db)
):
    """Create a new order"""
    order_service = OrderService(db)
    
    try:
        order = await order_service.create_order(order_data)
        
        return {
            "success": True,
            "order_id": order.order_id,
            "total_amount": order.total_amount / 100,  # Convert from paisa to NPR
            "payment_method": order.payment_method.value,
            "status": order.status.value,
            "message": "Order created successfully"
        }
    except Exception as e:
        logger.error("create_order_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create order")


def _can_access_order(order, current_user: Optional[dict], session_id_header: Optional[str]) -> bool:
    """Check if requester is authorized to access the order."""
    if current_user and order.user_id and order.user_id == current_user["id"]:
        return True
    if session_id_header and order.session_id and order.session_id == session_id_header.strip():
        return True
    return False


@router.get("/{order_id}")
@limiter.limit("60/minute")
async def get_order(
    request: Request,
    order_id: str,
    db: Database = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
):
    """Get order details. Requires X-Session-ID header matching order.session_id, or authenticated user matching order.user_id."""
    order_service = OrderService(db)
    order = await order_service.get_order_by_id(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not _can_access_order(order, current_user, x_session_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this order")

    return {
        "success": True,
        "order": {
            "order_id": order.order_id,
            "status": order.status.value,
            "payment_status": order.payment_status.value,
            "payment_method": order.payment_method.value,
            "total_amount": order.total_amount / 100,
            "delivery_address": order.delivery_address,
            "customer_phone": order.customer_phone,
            "courier_name": order.courier_name,
            "tracking_number": order.tracking_number,
            "created_at": order.created_at.isoformat()
        }
    }


@router.get("/{order_id}/tracking")
@limiter.limit("60/minute")
async def get_order_tracking(
    request: Request,
    order_id: str,
    db: Database = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
):
    """Get order tracking stages. Requires X-Session-ID or authenticated user matching order."""
    order_service = OrderService(db)
    order = await order_service.get_order_by_id(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not _can_access_order(order, current_user, x_session_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this order")

    status_val = order.status.value if hasattr(order.status, 'value') else str(order.status)

    all_stages = [
        {"id": "placed", "label": "Order Placed", "icon": "📋"},
        {"id": "confirmed", "label": "Confirmed", "icon": "✅"},
        {"id": "processing", "label": "Processing", "icon": "⚙️"},
        {"id": "dispatched", "label": "Dispatched", "icon": "🚚"},
        {"id": "out_for_delivery", "label": "Out for Delivery", "icon": "📦"},
        {"id": "delivered", "label": "Delivered", "icon": "🏠"},
    ]

    status_order = {s["id"]: i for i, s in enumerate(all_stages)}
    status_map = {
        "PENDING": "placed",
        "CONFIRMED": "confirmed",
        "PROCESSING": "processing",
        "DISPATCHED": "dispatched",
        "OUT_FOR_DELIVERY": "out_for_delivery",
        "DELIVERED": "delivered",
    }
    current_stage_id = status_map.get(status_val.upper(), "placed")
    current_idx = status_order.get(current_stage_id, 0)

    stages = []
    for i, stage in enumerate(all_stages):
        stages.append({
            **stage,
            "completed": i < current_idx,
            "current": i == current_idx,
            "timestamp": order.created_at.isoformat() if i <= current_idx else None,
        })

    destination = ""
    if order.delivery_address and isinstance(order.delivery_address, dict):
        destination = order.delivery_address.get("city", "")

    return {
        "order_id": order.order_id,
        "status": status_val,
        "stages": stages,
        "destination_city": destination,
        "estimated_delivery": None,
    }


@router.post("/track")
@limiter.limit("60/minute")
async def track_order(
    request: Request,
    body: OrderTrackRequest,
    db: Database = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
):
    """Track order by order ID or phone number. For order_id, requires X-Session-ID or auth. For phone_number, phone is the proof."""
    order_service = OrderService(db)

    if body.order_id:
        order = await order_service.get_order_by_id(body.order_id)
        if order and not _can_access_order(order, current_user, x_session_id):
            order = None
        orders = [order] if order else []
    elif body.phone_number:
        orders = await order_service.get_orders_by_phone(body.phone_number)
    else:
        raise HTTPException(status_code=400, detail="Provide order_id or phone_number")
    
    if not orders:
        return {
            "success": False,
            "message": "No orders found"
        }
    
    return {
        "success": True,
        "orders": [
            {
                "order_id": order.order_id,
                "status": order.status.value,
                "payment_status": order.payment_status.value,
                "total_amount": order.total_amount / 100,
                "courier_name": order.courier_name,
                "tracking_number": order.tracking_number,
                "created_at": order.created_at.isoformat()
            }
            for order in orders
        ]
    }

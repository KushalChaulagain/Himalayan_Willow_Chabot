from fastapi import APIRouter, Depends, HTTPException
import structlog

from app.models.order import OrderCreate, OrderTrackRequest
from app.services.orders import OrderService
from app.db.database import Database, get_db

logger = structlog.get_logger()
router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("/create")
async def create_order(
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


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    db: Database = Depends(get_db)
):
    """Get order details"""
    order_service = OrderService(db)
    
    order = await order_service.get_order_by_id(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
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
async def get_order_tracking(
    order_id: str,
    db: Database = Depends(get_db)
):
    """Get order tracking stages for the visual tracking map."""
    order_service = OrderService(db)
    order = await order_service.get_order_by_id(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

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
async def track_order(
    request: OrderTrackRequest,
    db: Database = Depends(get_db)
):
    """Track order by order ID or phone number"""
    order_service = OrderService(db)
    
    if request.order_id:
        order = await order_service.get_order_by_id(request.order_id)
        orders = [order] if order else []
    elif request.phone_number:
        orders = await order_service.get_orders_by_phone(request.phone_number)
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

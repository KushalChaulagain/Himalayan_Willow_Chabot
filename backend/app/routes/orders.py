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

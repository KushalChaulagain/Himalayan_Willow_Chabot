from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enum"""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentStatus(str, Enum):
    """Payment status enum"""
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, Enum):
    """Payment method enum"""
    ESEWA = "esewa"
    KHALTI = "khalti"
    COD = "cod"


class OrderItem(BaseModel):
    """Order item model"""
    product_id: int
    product_name: str
    product_sku: str
    unit_price: int  # in paisa
    quantity: int
    subtotal: int  # in paisa
    product_specifications: Optional[Dict] = None


class Order(BaseModel):
    """Order model"""
    id: Optional[int] = None
    order_id: str
    store_id: int = 1
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    payment_method: PaymentMethod
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_reference: Optional[str] = None
    subtotal: int  # in paisa
    discount: int = 0  # in paisa
    delivery_charge: int = 0  # in paisa
    total_amount: int  # in paisa
    delivery_address: Dict
    customer_phone: str
    customer_email: Optional[str] = None
    courier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrderCreate(BaseModel):
    """Order creation request"""
    session_id: str
    items: List[OrderItem]
    payment_method: PaymentMethod
    delivery_address: Dict
    customer_phone: str
    customer_email: Optional[str] = None


class OrderTrackRequest(BaseModel):
    """Order tracking request"""
    order_id: Optional[str] = None
    phone_number: Optional[str] = None

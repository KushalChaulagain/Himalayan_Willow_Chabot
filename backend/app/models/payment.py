from pydantic import BaseModel
from typing import Optional
from enum import Enum


class PaymentMethod(str, Enum):
    """Payment method enum"""
    ESEWA = "esewa"
    KHALTI = "khalti"
    COD = "cod"


class PaymentStatus(str, Enum):
    """Payment status enum"""
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentInitiateRequest(BaseModel):
    """Payment initiation request"""
    order_id: str
    payment_method: PaymentMethod
    amount: int  # in paisa
    customer_info: dict


class PaymentVerifyRequest(BaseModel):
    """Payment verification request"""
    order_id: str
    payment_method: PaymentMethod
    payment_reference: str


class PaymentResponse(BaseModel):
    """Payment response"""
    success: bool
    payment_url: Optional[str] = None
    payment_reference: Optional[str] = None
    message: str
    error: Optional[str] = None

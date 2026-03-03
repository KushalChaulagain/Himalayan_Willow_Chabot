from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
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


class CustomerInfo(BaseModel):
    """Customer info for payment initiation. Validates structure to prevent arbitrary data."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get for backward compatibility with .get() usage in routes."""
        val = getattr(self, key, default)
        return default if val is None else val


class PaymentInitiateRequest(BaseModel):
    """Payment initiation request"""
    order_id: str
    payment_method: PaymentMethod
    amount: int  # in paisa
    customer_info: CustomerInfo


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

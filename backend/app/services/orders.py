import random
import string
import structlog
from typing import List, Optional, Dict
from datetime import datetime

from app.db.database import Database
from app.models.order import Order, OrderItem, OrderCreate, OrderStatus, PaymentStatus

logger = structlog.get_logger()


class OrderService:
    """Order management service"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID in format HW-12345"""
        random_part = ''.join(random.choices(string.digits, k=5))
        return f"HW-{random_part}"
    
    async def create_order(self, order_data: OrderCreate) -> Order:
        """Create a new order"""
        
        # Generate order ID
        order_id = self._generate_order_id()
        
        # Calculate totals
        subtotal = sum(item.subtotal for item in order_data.items)
        delivery_charge = 0  # Free delivery for now
        total_amount = subtotal + delivery_charge
        
        # Insert order
        order_query = """
        INSERT INTO orders (
            order_id, session_id, status, payment_method, payment_status,
            subtotal, discount, delivery_charge, total_amount,
            delivery_address, customer_phone, customer_email
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING id, order_id, created_at
        """
        
        try:
            order_result = await self.db.fetch_one(
                order_query,
                order_id,
                order_data.session_id,
                OrderStatus.PENDING.value,
                order_data.payment_method.value,
                PaymentStatus.PENDING.value,
                subtotal,
                0,  # discount
                delivery_charge,
                total_amount,
                order_data.delivery_address,
                order_data.customer_phone,
                order_data.customer_email
            )
            
            # Insert order items
            item_query = """
            INSERT INTO order_items (
                order_id, product_id, product_name, product_sku,
                unit_price, quantity, subtotal, product_specifications
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """
            
            for item in order_data.items:
                await self.db.execute(
                    item_query,
                    order_result['id'],
                    item.product_id,
                    item.product_name,
                    item.product_sku,
                    item.unit_price,
                    item.quantity,
                    item.subtotal,
                    item.product_specifications
                )
            
            logger.info(
                "order_created",
                order_id=order_id,
                total_amount=total_amount,
                payment_method=order_data.payment_method.value
            )
            
            return Order(
                id=order_result['id'],
                order_id=order_id,
                session_id=order_data.session_id,
                status=OrderStatus.PENDING,
                payment_method=order_data.payment_method,
                payment_status=PaymentStatus.PENDING,
                subtotal=subtotal,
                delivery_charge=delivery_charge,
                total_amount=total_amount,
                delivery_address=order_data.delivery_address,
                customer_phone=order_data.customer_phone,
                customer_email=order_data.customer_email,
                created_at=order_result['created_at']
            )
            
        except Exception as e:
            logger.error("order_creation_failed", error=str(e))
            raise
    
    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get order by order ID"""
        query = """
        SELECT id, order_id, store_id, user_id, session_id, status,
               payment_method, payment_status, payment_reference,
               subtotal, discount, delivery_charge, total_amount,
               delivery_address, customer_phone, customer_email,
               courier_name, tracking_number, created_at
        FROM orders
        WHERE order_id = $1
        """
        
        try:
            row = await self.db.fetch_one(query, order_id)
            
            if not row:
                return None
            
            return Order(
                id=row['id'],
                order_id=row['order_id'],
                store_id=row['store_id'],
                user_id=row['user_id'],
                session_id=row['session_id'],
                status=OrderStatus(row['status']),
                payment_method=row['payment_method'],
                payment_status=PaymentStatus(row['payment_status']),
                payment_reference=row['payment_reference'],
                subtotal=row['subtotal'],
                discount=row['discount'],
                delivery_charge=row['delivery_charge'],
                total_amount=row['total_amount'],
                delivery_address=row['delivery_address'],
                customer_phone=row['customer_phone'],
                customer_email=row['customer_email'],
                courier_name=row['courier_name'],
                tracking_number=row['tracking_number'],
                created_at=row['created_at']
            )
            
        except Exception as e:
            logger.error("get_order_failed", error=str(e), order_id=order_id)
            return None
    
    async def update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        tracking_number: Optional[str] = None,
        courier_name: Optional[str] = None
    ) -> bool:
        """Update order status"""
        query = """
        UPDATE orders
        SET status = $1, tracking_number = $2, courier_name = $3, updated_at = NOW()
        WHERE order_id = $4
        """
        
        try:
            await self.db.execute(query, status.value, tracking_number, courier_name, order_id)
            logger.info("order_status_updated", order_id=order_id, status=status.value)
            return True
        except Exception as e:
            logger.error("update_order_status_failed", error=str(e), order_id=order_id)
            return False
    
    async def mark_order_as_paid(
        self,
        order_id: str,
        payment_reference: str
    ) -> bool:
        """Mark order as paid"""
        query = """
        UPDATE orders
        SET payment_status = $1, payment_reference = $2, status = $3, updated_at = NOW()
        WHERE order_id = $4
        """
        
        try:
            await self.db.execute(
                query,
                PaymentStatus.PAID.value,
                payment_reference,
                OrderStatus.CONFIRMED.value,
                order_id
            )
            logger.info("order_marked_paid", order_id=order_id, payment_reference=payment_reference)
            return True
        except Exception as e:
            logger.error("mark_order_paid_failed", error=str(e), order_id=order_id)
            return False
    
    async def get_orders_by_phone(self, phone_number: str) -> List[Order]:
        """Get orders by phone number"""
        query = """
        SELECT id, order_id, store_id, user_id, session_id, status,
               payment_method, payment_status, payment_reference,
               subtotal, discount, delivery_charge, total_amount,
               delivery_address, customer_phone, customer_email,
               courier_name, tracking_number, created_at
        FROM orders
        WHERE customer_phone = $1
        ORDER BY created_at DESC
        """
        
        try:
            rows = await self.db.fetch_all(query, phone_number)
            
            return [
                Order(
                    id=row['id'],
                    order_id=row['order_id'],
                    store_id=row['store_id'],
                    user_id=row['user_id'],
                    session_id=row['session_id'],
                    status=OrderStatus(row['status']),
                    payment_method=row['payment_method'],
                    payment_status=PaymentStatus(row['payment_status']),
                    payment_reference=row['payment_reference'],
                    subtotal=row['subtotal'],
                    discount=row['discount'],
                    delivery_charge=row['delivery_charge'],
                    total_amount=row['total_amount'],
                    delivery_address=row['delivery_address'],
                    customer_phone=row['customer_phone'],
                    customer_email=row['customer_email'],
                    courier_name=row['courier_name'],
                    tracking_number=row['tracking_number'],
                    created_at=row['created_at']
                )
                for row in rows
            ]
            
        except Exception as e:
            logger.error("get_orders_by_phone_failed", error=str(e))
            return []

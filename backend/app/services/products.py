from typing import List, Optional, Dict
import structlog
from app.db.database import Database
from app.models.product import Product, ProductCard

logger = structlog.get_logger()


class ProductService:
    """Product search and management service"""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def search_products(
        self,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_rating: float = 0.0,
        limit: int = 5
    ) -> List[Product]:
        """Search products with filters"""
        
        query = """
        SELECT id, store_id, sku, name, category, subcategory, description,
               price, original_price, in_stock, stock_quantity, rating,
               review_count, sales_count, image_url, specifications,
               created_at
        FROM products
        WHERE in_stock = true
        """
        
        params = []
        param_count = 1
        
        if category:
            query += f" AND category = ${param_count}"
            params.append(category)
            param_count += 1
        
        if max_price:
            query += f" AND price <= ${param_count}"
            params.append(max_price)
            param_count += 1
        
        if min_rating > 0:
            query += f" AND rating >= ${param_count}"
            params.append(min_rating)
            param_count += 1
        
        query += " ORDER BY rating DESC, sales_count DESC"
        query += f" LIMIT ${param_count}"
        params.append(limit)
        
        try:
            results = await self.db.fetch_all(query, *params)
            
            products = [
                Product(
                    id=row['id'],
                    store_id=row['store_id'],
                    sku=row['sku'],
                    name=row['name'],
                    category=row['category'],
                    subcategory=row['subcategory'],
                    description=row['description'],
                    price=float(row['price']),
                    original_price=float(row['original_price']) if row['original_price'] else None,
                    in_stock=row['in_stock'],
                    stock_quantity=row['stock_quantity'],
                    rating=float(row['rating']),
                    review_count=row['review_count'],
                    sales_count=row['sales_count'],
                    image_url=row['image_url'],
                    specifications=row['specifications'],
                    created_at=row['created_at']
                )
                for row in results
            ]
            
            logger.info(
                "products_searched",
                category=category,
                max_price=max_price,
                results_count=len(products)
            )
            
            return products
            
        except Exception as e:
            logger.error("product_search_failed", error=str(e))
            return []
    
    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        query = """
        SELECT id, store_id, sku, name, category, subcategory, description,
               price, original_price, in_stock, stock_quantity, rating,
               review_count, sales_count, image_url, specifications,
               created_at
        FROM products
        WHERE id = $1
        """
        
        try:
            row = await self.db.fetch_one(query, product_id)
            
            if not row:
                return None
            
            return Product(
                id=row['id'],
                store_id=row['store_id'],
                sku=row['sku'],
                name=row['name'],
                category=row['category'],
                subcategory=row['subcategory'],
                description=row['description'],
                price=float(row['price']),
                original_price=float(row['original_price']) if row['original_price'] else None,
                in_stock=row['in_stock'],
                stock_quantity=row['stock_quantity'],
                rating=float(row['rating']),
                review_count=row['review_count'],
                sales_count=row['sales_count'],
                image_url=row['image_url'],
                specifications=row['specifications'],
                created_at=row['created_at']
            )
            
        except Exception as e:
            logger.error("get_product_failed", error=str(e), product_id=product_id)
            return None
    
    def create_product_card(self, product: Product, reason: str = "") -> ProductCard:
        """Create product card for chat response"""
        return ProductCard(
            id=product.id,
            name=product.name,
            price=product.price,
            image_url=product.image_url,
            reason=reason or f"Highly rated {product.category} with {product.review_count} reviews",
            in_stock=product.in_stock,
            specifications=product.specifications
        )
    
    async def get_popular_products(self, limit: int = 5) -> List[Product]:
        """Get popular products by sales count"""
        query = """
        SELECT id, store_id, sku, name, category, subcategory, description,
               price, original_price, in_stock, stock_quantity, rating,
               review_count, sales_count, image_url, specifications,
               created_at
        FROM products
        WHERE in_stock = true
        ORDER BY sales_count DESC, rating DESC
        LIMIT $1
        """
        
        try:
            results = await self.db.fetch_all(query, limit)
            
            return [
                Product(
                    id=row['id'],
                    store_id=row['store_id'],
                    sku=row['sku'],
                    name=row['name'],
                    category=row['category'],
                    subcategory=row['subcategory'],
                    description=row['description'],
                    price=float(row['price']),
                    original_price=float(row['original_price']) if row['original_price'] else None,
                    in_stock=row['in_stock'],
                    stock_quantity=row['stock_quantity'],
                    rating=float(row['rating']),
                    review_count=row['review_count'],
                    sales_count=row['sales_count'],
                    image_url=row['image_url'],
                    specifications=row['specifications'],
                    created_at=row['created_at']
                )
                for row in results
            ]
            
        except Exception as e:
            logger.error("get_popular_products_failed", error=str(e))
            return []

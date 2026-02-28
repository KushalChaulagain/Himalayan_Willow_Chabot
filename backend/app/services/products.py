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
        willow_type: Optional[str] = None,
        weight_min: Optional[int] = None,
        weight_max: Optional[int] = None,
        player_level: Optional[str] = None,
        limit: int = 5
    ) -> List[Product]:
        """Search products with filters including cricket-specific specs."""
        
        query = """
        SELECT id, store_id, sku, name, category, subcategory, description,
               price, original_price, in_stock, stock_quantity, rating,
               review_count, sales_count, image_url, specifications,
               created_at
        FROM products
        WHERE in_stock = true
        """
        
        params: list = []
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
        
        if willow_type:
            query += f" AND specifications->>'bat_type' ILIKE ${param_count}"
            params.append(f"%{willow_type}%")
            param_count += 1
        
        if weight_min is not None or weight_max is not None:
            if weight_min is not None:
                query += f" AND COALESCE((NULLIF(SUBSTRING(COALESCE(specifications->>'weight','') FROM '[0-9]+'), '')::int), 0) >= ${param_count}"
                params.append(weight_min)
                param_count += 1
            if weight_max is not None:
                query += f" AND COALESCE((NULLIF(SUBSTRING(COALESCE(specifications->>'weight','') FROM '[0-9]+'), '')::int), 9999) <= ${param_count}"
                params.append(weight_max)
                param_count += 1
        
        if player_level:
            query += f" AND specifications->>'suitable_for' ILIKE ${param_count}"
            params.append(f"%{player_level}%")
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
    
    async def get_products_by_ids(self, product_ids: List[int]) -> List[Product]:
        """Get multiple products by IDs (for cart display). Returns in order of request."""
        if not product_ids:
            return []
        seen = set()
        unique_ids = []
        for pid in product_ids:
            if pid not in seen:
                seen.add(pid)
                unique_ids.append(pid)
        placeholders = ",".join(f"${i+1}" for i in range(len(unique_ids)))
        query = f"""
        SELECT id, store_id, sku, name, category, subcategory, description,
               price, original_price, in_stock, stock_quantity, rating,
               review_count, sales_count, image_url, specifications,
               created_at
        FROM products
        WHERE id IN ({placeholders})
        """
        try:
            results = await self.db.fetch_all(query, *unique_ids)
            by_id = {
                row["id"]: Product(
                    id=row["id"],
                    store_id=row["store_id"],
                    sku=row["sku"],
                    name=row["name"],
                    category=row["category"],
                    subcategory=row["subcategory"],
                    description=row["description"],
                    price=float(row["price"]),
                    original_price=float(row["original_price"]) if row["original_price"] else None,
                    in_stock=row["in_stock"],
                    stock_quantity=row["stock_quantity"],
                    rating=float(row["rating"]),
                    review_count=row["review_count"],
                    sales_count=row["sales_count"],
                    image_url=row["image_url"],
                    specifications=row["specifications"],
                    created_at=row["created_at"],
                )
                for row in results
            }
            return [by_id[pid] for pid in unique_ids if pid in by_id]
        except Exception as e:
            logger.error("get_products_by_ids_failed", error=str(e), product_ids=product_ids)
            return []
    
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

    async def get_products_summary_for_context(
        self, category: Optional[str] = None, limit: int = 50
    ) -> List[Dict]:
        """
        Get a compact product summary for LLM context (e.g. visual search).
        Returns list of {id, name, category, price} for in-stock products.
        """
        query = """
        SELECT id, name, category, price
        FROM products
        WHERE in_stock = true
        """
        params: list = []
        if category:
            query += " AND category = $1"
            params.append(category)
        query += " ORDER BY rating DESC, sales_count DESC"
        query += f" LIMIT ${len(params) + 1}"
        params.append(limit)

        try:
            results = await self.db.fetch_all(query, *params)
            return [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "category": row["category"],
                    "price": float(row["price"]),
                }
                for row in results
            ]
        except Exception as e:
            logger.error("get_products_summary_failed", error=str(e))
            return []

    async def get_storefront_mix(self, limit: int = 6) -> List[Product]:
        """Top seller per category, then fill remaining slots by popularity.

        Ensures the storefront showcases product diversity instead of
        potentially showing 6 items from the same category.
        """
        query = """
        WITH ranked AS (
            SELECT id, store_id, sku, name, category, subcategory, description,
                   price, original_price, in_stock, stock_quantity, rating,
                   review_count, sales_count, image_url, specifications, created_at,
                   ROW_NUMBER() OVER (PARTITION BY category ORDER BY sales_count DESC, rating DESC) AS rn
            FROM products
            WHERE in_stock = true
        )
        SELECT id, store_id, sku, name, category, subcategory, description,
               price, original_price, in_stock, stock_quantity, rating,
               review_count, sales_count, image_url, specifications,
               created_at
        FROM ranked
        WHERE rn = 1
        ORDER BY sales_count DESC, rating DESC
        LIMIT $1
        """

        try:
            results = await self.db.fetch_all(query, limit)

            products = [
                Product(
                    id=row["id"],
                    store_id=row["store_id"],
                    sku=row["sku"],
                    name=row["name"],
                    category=row["category"],
                    subcategory=row["subcategory"],
                    description=row["description"],
                    price=float(row["price"]),
                    original_price=float(row["original_price"]) if row["original_price"] else None,
                    in_stock=row["in_stock"],
                    stock_quantity=row["stock_quantity"],
                    rating=float(row["rating"]),
                    review_count=row["review_count"],
                    sales_count=row["sales_count"],
                    image_url=row["image_url"],
                    specifications=row["specifications"],
                    created_at=row["created_at"],
                )
                for row in results
            ]

            if len(products) < limit:
                existing_ids = {p.id for p in products}
                extra = await self.get_popular_products(limit=limit * 2)
                for p in extra:
                    if p.id not in existing_ids:
                        products.append(p)
                        existing_ids.add(p.id)
                    if len(products) >= limit:
                        break

            return products[:limit]

        except Exception as e:
            logger.error("get_storefront_mix_failed", error=str(e))
            return await self.get_popular_products(limit=limit)

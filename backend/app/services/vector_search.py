"""
ChromaDB-backed semantic product search with metadata filtering
for Price Range and Willow Type.
"""
from typing import List, Optional, Dict, Any
import structlog

logger = structlog.get_logger()

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("chromadb_not_installed_semantic_search_disabled")


class VectorSearchService:
    """Persistent ChromaDB collection for semantic product search."""

    def __init__(self, persist_directory: str = "./chroma_db"):
        self._collection = None
        if not CHROMA_AVAILABLE:
            return

        try:
            self._client = chromadb.Client(
                ChromaSettings(
                    anonymized_telemetry=False,
                    is_persistent=True,
                    persist_directory=persist_directory,
                )
            )
            self._collection = self._client.get_or_create_collection(
                name="products",
                metadata={"description": "Cricket product embeddings for semantic search"},
            )
            logger.info("chromadb_initialized", persist_directory=persist_directory)
        except Exception as e:
            logger.error("chromadb_init_failed", error=str(e))

    @property
    def is_available(self) -> bool:
        return self._collection is not None

    def index_product(self, product: Dict[str, Any]) -> None:
        """Upsert a product into the vector collection with rich metadata."""
        if not self.is_available:
            return

        specs = product.get("specifications") or {}
        willow_type = (
            specs.get("bat_type", "")
            or specs.get("willow_type", "")
            or ""
        )
        player_level = (
            specs.get("suitable_for", "")
            or specs.get("player_level", "")
            or ""
        )

        product_text = (
            f"{product['name']}\n"
            f"Category: {product.get('category', '')}\n"
            f"Description: {product.get('description', '')}\n"
            f"Specifications: {' '.join(f'{k}: {v}' for k, v in specs.items())}\n"
            f"Price: NPR {product.get('price', 0)}"
        )

        metadata: Dict[str, Any] = {
            "product_id": int(product["id"]),
            "category": product.get("category", ""),
            "price": float(product.get("price", 0)),
            "in_stock": bool(product.get("in_stock", True)),
        }
        if willow_type:
            metadata["willow_type"] = willow_type
        if player_level:
            metadata["player_level"] = player_level

        try:
            self._collection.upsert(
                documents=[product_text],
                metadatas=[metadata],
                ids=[f"product_{product['id']}"],
            )
        except Exception as e:
            logger.error("chromadb_index_failed", product_id=product["id"], error=str(e))

    def search_products_semantic(
        self,
        query: str,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        willow_type: Optional[str] = None,
        player_level: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Semantic similarity search with optional metadata filters.

        Supported filters:
          - price range via min_price / max_price
          - willow_type  (e.g. "English Willow", "Kashmir Willow")
          - category     (e.g. "bat", "ball", "gloves")
        """
        if not self.is_available:
            return []

        where_clauses: List[Dict] = [{"in_stock": True}]

        if min_price is not None:
            where_clauses.append({"price": {"$gte": min_price}})
        if max_price is not None:
            where_clauses.append({"price": {"$lte": max_price}})
        if willow_type:
            where_clauses.append({"willow_type": willow_type})
        if player_level:
            where_clauses.append({"player_level": player_level})
        if category:
            where_clauses.append({"category": category})

        where: Optional[Dict] = None
        if len(where_clauses) == 1:
            where = where_clauses[0]
        elif len(where_clauses) > 1:
            where = {"$and": where_clauses}

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=limit,
                where=where,
            )

            if not results or not results.get("metadatas"):
                return []

            return results["metadatas"][0]
        except Exception as e:
            logger.error("chromadb_search_failed", error=str(e), query=query[:100])
            return []

    def bulk_index(self, products: List[Dict[str, Any]]) -> int:
        """Index multiple products. Returns count of successfully indexed items."""
        count = 0
        for product in products:
            try:
                self.index_product(product)
                count += 1
            except Exception:
                continue
        logger.info("chromadb_bulk_index_complete", indexed=count, total=len(products))
        return count


vector_search_service = VectorSearchService()

import asyncpg
from typing import Optional
import structlog

from app.config import settings

logger = structlog.get_logger()


class DatabaseUnavailableError(RuntimeError):
    """Raised when an operation requires the database but it is not connected."""
    pass


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create database connection pool. Skips if DATABASE_URL is empty."""
        if not (getattr(settings, "database_url", None) or "").strip():
            logger.warning("database_skipped", reason="DATABASE_URL not set")
            return
        try:
            self.pool = await asyncpg.create_pool(
                dsn=settings.database_url,
                min_size=1,
                max_size=20,
                command_timeout=10.0,
                max_queries=50000,
                max_inactive_connection_lifetime=300.0
            )
            logger.info("database_connected", pool_size=self.pool.get_size())
        except Exception as e:
            logger.warning(
                "database_connection_failed_running_without_db",
                error=str(e),
                hint="Set DATABASE_URL in .env for orders/persistence; chat works without DB."
            )
            self.pool = None
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("database_disconnected")

    @property
    def is_available(self) -> bool:
        """True if database pool is connected and usable."""
        return self.pool is not None

    async def fetch_one(self, query: str, *args):
        """Fetch single row"""
        if self.pool is None:
            raise DatabaseUnavailableError("Database is not configured or unavailable.")
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetch_all(self, query: str, *args):
        """Fetch all rows"""
        if self.pool is None:
            raise DatabaseUnavailableError("Database is not configured or unavailable.")
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute(self, query: str, *args):
        """Execute query without returning results"""
        if self.pool is None:
            raise DatabaseUnavailableError("Database is not configured or unavailable.")
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def execute_many(self, query: str, args_list):
        """Execute query multiple times with different arguments"""
        if self.pool is None:
            raise DatabaseUnavailableError("Database is not configured or unavailable.")
        async with self.pool.acquire() as conn:
            return await conn.executemany(query, args_list)


# Global database instance
db = Database()


async def get_db() -> Database:
    """Dependency to get database instance"""
    return db

import asyncpg
from typing import Optional
import structlog

from app.config import settings

logger = structlog.get_logger()


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                dsn=settings.database_url,
                min_size=5,
                max_size=20,
                command_timeout=10.0,
                max_queries=50000,
                max_inactive_connection_lifetime=300.0
            )
            logger.info("database_connected", pool_size=self.pool.get_size())
        except Exception as e:
            logger.error("database_connection_failed", error=str(e))
            raise
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("database_disconnected")
    
    async def fetch_one(self, query: str, *args):
        """Fetch single row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetch_all(self, query: str, *args):
        """Fetch all rows"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute(self, query: str, *args):
        """Execute query without returning results"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def execute_many(self, query: str, args_list):
        """Execute query multiple times with different arguments"""
        async with self.pool.acquire() as conn:
            return await conn.executemany(query, args_list)


# Global database instance
db = Database()


async def get_db() -> Database:
    """Dependency to get database instance"""
    return db

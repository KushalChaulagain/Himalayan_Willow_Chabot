import asyncio
import asyncpg
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


async def run_migrations():
    """Run database migrations"""
    print(f"Connecting to database: {settings.database_url}")
    
    try:
        conn = await asyncpg.connect(settings.database_url)
        print("Connected to database successfully")
        
        migrations_dir = Path(__file__).parent.parent / "migrations"
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        if not migration_files:
            print("No migration files found")
            return
        
        for migration_file in migration_files:
            print(f"\nRunning migration: {migration_file.name}")
            
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            try:
                await conn.execute(sql)
                print(f"✓ Migration {migration_file.name} completed successfully")
            except Exception as e:
                print(f"✗ Migration {migration_file.name} failed: {e}")
                raise
        
        print("\n✓ All migrations completed successfully")
        
        await conn.close()
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_migrations())

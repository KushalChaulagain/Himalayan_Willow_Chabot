import asyncio
import asyncpg
from pathlib import Path


async def run_migration_002():
    """Run only the 002_sales_enhancements migration"""
    
    # Read database URL from .env file
    env_file = Path(__file__).parent.parent / ".env"
    database_url = None
    
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                database_url = line.split('=', 1)[1].strip()
                break
    
    if not database_url:
        print("ERROR: DATABASE_URL not found in .env file")
        return
    
    print(f"Connecting to database...")
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✓ Connected to database successfully")
        
        migration_file = Path(__file__).parent.parent / "migrations" / "002_sales_enhancements.sql"
        
        if not migration_file.exists():
            print(f"ERROR: Migration file not found: {migration_file}")
            return
        
        print(f"\nRunning migration: {migration_file.name}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        try:
            await conn.execute(sql)
            print(f"✓ Migration {migration_file.name} completed successfully")
        except Exception as e:
            print(f"✗ Migration {migration_file.name} failed: {e}")
            raise
        
        print("\n✓ Sales enhancement tables created successfully!")
        print("\nNew tables created:")
        print("  - user_profiles")
        print("  - session_analytics")
        print("  - product_recommendations")
        print("  - conversion_metrics")
        print("  - product_bundles")
        
        await conn.close()
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_migration_002())

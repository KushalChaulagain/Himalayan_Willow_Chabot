#!/usr/bin/env python3
"""
Database Migration Runner for Himalayan Willow Chatbot
Runs SQL migration files in order
"""
import asyncio
import asyncpg
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found in .env file")
    print("Please add DATABASE_URL to your .env file")
    sys.exit(1)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def run_migrations():
    """Run all SQL migration files in order"""
    
    print("🔄 Connecting to database...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database successfully\n")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        # Get all migration files sorted by name
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        
        if not migration_files:
            print("⚠️  No migration files found in migrations/ directory")
            return
        
        print(f"📁 Found {len(migration_files)} migration file(s)\n")
        
        for migration_file in migration_files:
            print(f"🔧 Running migration: {migration_file.name}")
            
            # Read migration SQL
            sql_content = migration_file.read_text(encoding="utf-8")
            
            try:
                # Execute migration
                await conn.execute(sql_content)
                print(f"   ✅ {migration_file.name} completed successfully")
            except Exception as e:
                print(f"   ❌ {migration_file.name} failed: {e}")
                raise
        
        print("\n" + "="*60)
        print("✅ All migrations completed successfully!")
        print("="*60)
        
        # Show table count
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        print(f"\n📊 Database now has {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        await conn.close()
        print("\n🔌 Database connection closed")


if __name__ == "__main__":
    print("="*60)
    print("🚀 Himalayan Willow - Database Migration Runner")
    print("="*60 + "\n")
    
    asyncio.run(run_migrations())

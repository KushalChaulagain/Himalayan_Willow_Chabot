#!/usr/bin/env python3
"""
Run migration 002 only - Sales Enhancement Schema
"""
import asyncio
import asyncpg
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

async def run_migration_002():
    """Run migration 002 SQL file"""
    
    print("🔄 Connecting to database...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database successfully\n")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        migration_file = Path(__file__).parent / "migrations" / "002_sales_enhancements.sql"
        
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            sys.exit(1)
        
        print(f"🔧 Running migration: 002_sales_enhancements.sql")
        
        # Read migration SQL
        sql_content = migration_file.read_text(encoding="utf-8")
        
        # Execute migration
        await conn.execute(sql_content)
        print(f"   ✅ Migration completed successfully\n")
        
        print("="*60)
        print("✅ Migration 002 completed successfully!")
        print("="*60)
        
        # Show new tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND table_name IN ('user_profiles', 'session_analytics', 'product_recommendations', 
                               'conversion_metrics', 'product_bundles')
            ORDER BY table_name
        """)
        
        print(f"\n📊 New tables created ({len(tables)}):")
        for table in tables:
            print(f"   ✅ {table['table_name']}")
        
        # Check if columns were added
        print("\n📝 Checking column additions...")
        
        # Check related_products column in products table
        col_check = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'products' 
            AND column_name = 'related_products'
        """)
        
        if col_check > 0:
            print("   ✅ products.related_products column added")
        
        # Check recommendation_context column in chat_messages table
        col_check2 = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'chat_messages' 
            AND column_name = 'recommendation_context'
        """)
        
        if col_check2 > 0:
            print("   ✅ chat_messages.recommendation_context column added")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        await conn.close()
        print("\n🔌 Database connection closed")


if __name__ == "__main__":
    print("="*60)
    print("🚀 Running Migration 002: Sales Enhancements")
    print("="*60 + "\n")
    
    asyncio.run(run_migration_002())

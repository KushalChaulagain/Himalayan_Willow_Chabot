#!/usr/bin/env python3
"""
Check current database status
"""
import asyncio
import asyncpg
import sys
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

async def check_db():
    """Check database tables and structure"""
    
    print("🔄 Connecting to database...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database successfully\n")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        # Get all tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        print(f"📊 Current database has {len(tables)} tables:\n")
        
        for table in tables:
            table_name = table['table_name']
            
            # Get row count
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            
            print(f"   ✅ {table_name} ({count} rows)")
        
        print("\n" + "="*60)
        
        # Check if new tables from migration 002 exist
        new_tables = ['user_profiles', 'session_analytics', 'product_recommendations', 
                      'conversion_metrics', 'product_bundles']
        
        existing_table_names = [t['table_name'] for t in tables]
        missing_tables = [t for t in new_tables if t not in existing_table_names]
        
        if missing_tables:
            print(f"\n⚠️  Missing tables from migration 002:")
            for table in missing_tables:
                print(f"   - {table}")
            print("\n💡 Run migration 002 to create these tables")
        else:
            print("\n✅ All tables from migration 002 are present")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_db())

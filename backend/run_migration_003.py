#!/usr/bin/env python3
"""
Run migration 003 only - Google Auth (users table)
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

try:
    import asyncpg
except ImportError:
    print("❌ asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)

DATABASE_URL = os.getenv("DATABASE_URL", "")


async def run_migration_003():
    """Run migration 003 SQL file"""
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set in .env")
        sys.exit(1)

    print("🔄 Connecting to database...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to database successfully\n")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)

    try:
        migration_file = Path(__file__).parent / "migrations" / "003_google_auth.sql"

        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            sys.exit(1)

        print("🔧 Running migration: 003_google_auth.sql")

        sql_content = migration_file.read_text(encoding="utf-8")

        # Run statements one by one to handle FK that might already exist
        statements = []
        current = []
        for line in sql_content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("--") or not stripped:
                continue
            current.append(line)
            if stripped.endswith(";"):
                stmt = "\n".join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
        if current:
            statements.append("\n".join(current).strip())

        for stmt in statements:
            try:
                await conn.execute(stmt)
            except asyncpg.exceptions.DuplicateObjectError:
                # Constraint or object already exists
                if "fk_chat_sessions_user" in stmt:
                    print("   ⚠️  FK constraint already exists, skipping")
                else:
                    raise

        print("   ✅ Migration completed successfully\n")
        print("=" * 60)
        print("✅ Migration 003 completed successfully!")
        print("=" * 60)

        tables = await conn.fetch(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            AND table_name = 'users'
        """
        )
        if tables:
            print("\n📊 New table: users")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        await conn.close()
        print("\n🔌 Database connection closed")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Running Migration 003: Google Auth")
    print("=" * 60 + "\n")

    asyncio.run(run_migration_003())

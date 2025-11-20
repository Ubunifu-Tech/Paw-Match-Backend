"""
Database Initialization Script

This script creates all database tables based on SQLAlchemy models.
Run this once to set up your database schema.

Usage:
    python scripts/init_database.py

Note: Make sure your DATABASE_URL is set in .env before running this script.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import engine, Base
from app.db.models import User, Session, ChatMessage, SavedResult, Breed, BreedImage
from app.db.models.favorite import Favorite
from app.db.models.api_usage import APIUsage
from sqlalchemy import text


async def init_db():
    """Create all database tables"""
    print("🚀 Initializing database...")
    
    try:
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version}")
        
        # Create all tables
        async with engine.begin() as conn:
            print("📋 Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database initialized successfully!")
        print("\nCreated tables:")
        print("  - users")
        print("  - sessions")
        print("  - chat_messages")
        print("  - saved_results")
        print("  - breeds")
        print("  - breed_images")
        print("  - favorites")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


async def drop_all_tables():
    """Drop all tables (use with caution!)"""
    print("⚠️  WARNING: This will delete all data!")
    response = input("Type 'yes' to confirm: ")
    
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    try:
        async with engine.begin() as conn:
            print("🗑️  Dropping all tables...")
            await conn.run_sync(Base.metadata.drop_all)
        
        print("✅ All tables dropped")
        
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database initialization tool')
    parser.add_argument('--drop', action='store_true', help='Drop all tables (DESTRUCTIVE)')
    args = parser.parse_args()
    
    if args.drop:
        asyncio.run(drop_all_tables())
    else:
        asyncio.run(init_db())

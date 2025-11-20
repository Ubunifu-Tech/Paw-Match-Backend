"""
Database Query Script - Check Local Database Content

This script queries your local database to see what data exists
and what needs to be loaded into production.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load .env file first
from dotenv import load_dotenv
load_dotenv()

# Set minimal env vars if not present
if not os.getenv('GEMINI_API_KEY'):
    os.environ['GEMINI_API_KEY'] = 'dummy_key_for_db_query'
if not os.getenv('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'dummy_key_for_db_query'

from sqlalchemy import text
from app.core.database import engine


async def query_database():
    """Query the database and show what's there"""
    
    print("=" * 80)
    print("DATABASE CONTENT ANALYSIS")
    print("=" * 80)
    print()
    
    try:
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT current_database(), version()"))
            db_info = result.fetchone()
            print(f"✅ Connected to database: {db_info[0]}")
            print(f"   PostgreSQL: {db_info[1].split(',')[0]}")
            print()
            
            # Check tables
            print("📋 TABLES AND ROW COUNTS")
            print("-" * 80)
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                print("❌ No tables found in database!")
                print("\n💡 SOLUTION:")
                print("   1. Initialize database: python3 scripts/init_database.py")
                print("   2. Load breed data: python3 populate_breeds.py")
                return
            
            table_counts = {}
            for table in tables:
                try:
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    table_counts[table] = count
                    status = "✅" if count > 0 else "⚪"
                    print(f"{status} {table:25} {count:>8,} rows")
                except Exception as e:
                    print(f"❌ {table:25} Error: {str(e)[:40]}")
            
            print()
            
            # Detailed analysis
            print("🔍 DATA ANALYSIS FOR PRODUCTION")
            print("=" * 80)
            
            # Breeds
            if 'breeds' in table_counts:
                breed_count = table_counts['breeds']
                print(f"\n🐕 BREEDS: {breed_count} total")
                if breed_count > 0:
                    result = await conn.execute(text("""
                        SELECT name, 
                               LEFT(description, 50) as desc_preview
                        FROM breeds 
                        ORDER BY name 
                        LIMIT 5
                    """))
                    print("   Sample:")
                    for row in result.fetchall():
                        desc = row[1] + "..." if row[1] else "No description"
                        print(f"      • {row[0]:30} {desc}")
                    if breed_count > 5:
                        print(f"      ... and {breed_count - 5} more")
                    print(f"\n   ✅ MUST LOAD: This data is critical for the app")
                    print(f"      Command: railway run python3 populate_breeds.py")
                else:
                    print("   ⚠️  EMPTY! Run: python3 populate_breeds.py")
            else:
                print("\n❌ BREEDS table not found!")
            
            # Breed Images
            if 'breed_images' in table_counts:
                image_count = table_counts['breed_images']
                print(f"\n🖼️  BREED IMAGES: {image_count} total")
                if image_count > 0:
                    result = await conn.execute(text("""
                        SELECT breed_id, url, COUNT(*) OVER() as total
                        FROM breed_images 
                        LIMIT 3
                    """))
                    print("   Sample:")
                    for row in result.fetchall():
                        url = row[1][:60] + "..." if len(row[1]) > 60 else row[1]
                        print(f"      • Breed ID: {row[0]} - {url}")
                    print(f"\n   📦 RECOMMENDED: Upload images to GCS/S3 for production")
                else:
                    print("   ⚪ Empty - images will load on demand")
            
            # Users
            if 'users' in table_counts:
                user_count = table_counts['users']
                print(f"\n👤 USERS: {user_count} total")
                if user_count > 0:
                    result = await conn.execute(text("""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(*) FILTER (WHERE is_anonymous = true) as anon,
                            COUNT(*) FILTER (WHERE is_anonymous = false) as registered
                        FROM users
                    """))
                    stats = result.fetchone()
                    print(f"   Anonymous: {stats[1]}")
                    print(f"   Registered: {stats[2]}")
                    print(f"\n   🚫 SKIP: This is test/development data")
                    print(f"      Production users will be created fresh")
                else:
                    print("   ⚪ Empty - fresh database")
            
            # Sessions
            if 'sessions' in table_counts:
                session_count = table_counts['sessions']
                print(f"\n💬 CHAT SESSIONS: {session_count} total")
                if session_count > 0:
                    print(f"   🚫 SKIP: Test sessions - production starts fresh")
                else:
                    print("   ⚪ Empty")
            
            # Saved Results
            if 'saved_results' in table_counts:
                results_count = table_counts['saved_results']
                print(f"\n⭐ SAVED RESULTS: {results_count} total")
                if results_count > 0:
                    print(f"   🚫 SKIP: Test data - production starts fresh")
                else:
                    print("   ⚪ Empty")
            
            # Favorites
            if 'favorites' in table_counts:
                fav_count = table_counts['favorites']
                print(f"\n❤️  FAVORITES: {fav_count} total")
                if fav_count > 0:
                    print(f"   🚫 SKIP: Test data - production starts fresh")
                else:
                    print("   ⚪ Empty")
            
            # Summary
            print("\n" + "=" * 80)
            print("📝 PRODUCTION DEPLOYMENT CHECKLIST")
            print("=" * 80)
            
            breed_ready = 'breeds' in table_counts and table_counts['breeds'] > 0
            
            if breed_ready:
                print("\n✅ YOU'RE READY TO DEPLOY!")
                print("\n📦 What to load in production:")
                print(f"   1. Breed data ({table_counts['breeds']} breeds) - CRITICAL")
                if 'breed_images' in table_counts and table_counts['breed_images'] > 0:
                    print(f"   2. Breed images ({table_counts['breed_images']} images) - Optional")
                
                print("\n🚀 Deployment steps:")
                print("   1. Push code to GitHub")
                print("   2. Railway auto-deploys")
                print("   3. Tables auto-create on first run")
                print("   4. Load breeds: railway run python3 populate_breeds.py")
                print("   5. Test: https://your-app.up.railway.app/api/breeds")
                
            else:
                print("\n⚠️  NOT READY YET!")
                print("\n📋 TODO before deploying:")
                print("   1. Load breed data: python3 populate_breeds.py")
                print("   2. Verify data: python3 scripts/query_local_db.py")
                print("   3. Then deploy to Railway")
            
            # Data that STAYS local (don't transfer)
            skip_data = []
            if 'users' in table_counts and table_counts['users'] > 0:
                skip_data.append(f"users ({table_counts['users']})")
            if 'sessions' in table_counts and table_counts['sessions'] > 0:
                skip_data.append(f"sessions ({table_counts['sessions']})")
            if 'saved_results' in table_counts and table_counts['saved_results'] > 0:
                skip_data.append(f"saved_results ({table_counts['saved_results']})")
            if 'favorites' in table_counts and table_counts['favorites'] > 0:
                skip_data.append(f"favorites ({table_counts['favorites']})")
            
            if skip_data:
                print(f"\n🚫 Test data (DON'T transfer to prod):")
                for item in skip_data:
                    print(f"   • {item}")
            
            print()
            
    except Exception as e:
        print(f"\n❌ ERROR connecting to database:")
        print(f"   {str(e)}")
        print("\n💡 Possible solutions:")
        print("   1. Check PostgreSQL is running:")
        print("      brew services start postgresql")
        print("   2. Verify DATABASE_URL in .env file")
        print("   3. Create database if it doesn't exist:")
        print("      createdb dogmatch")
        print("   4. Initialize tables:")
        print("      python3 scripts/init_database.py")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print()
    asyncio.run(query_database())
    print()

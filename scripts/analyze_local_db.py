"""
Local Database Analysis Script

This script analyzes your local PostgreSQL database to determine what data
needs to be loaded into production.

It will:
1. Check all tables and their row counts
2. Export schema information
3. Identify which tables have data
4. Generate recommendations for data loading
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text, inspect
from app.core.database import engine
from app.core.config import get_settings


async def analyze_database():
    """Analyze the local database and generate a report"""
    
    settings = get_settings()
    print("=" * 80)
    print("LOCAL DATABASE ANALYSIS REPORT")
    print("=" * 80)
    print(f"\nDatabase URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'hidden'}")
    print()
    
    try:
        async with engine.begin() as conn:
            # 1. Test connection and get database info
            print("📊 DATABASE CONNECTION")
            print("-" * 80)
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"PostgreSQL Version: {version.split(',')[0]}")
            
            result = await conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"Database Name: {db_name}")
            print()
            
            # 2. List all tables
            print("📋 TABLES IN DATABASE")
            print("-" * 80)
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                print("⚠️  No tables found! Database needs to be initialized.")
                print("\nRun: python scripts/init_database.py")
                return
            
            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  • {table}")
            print()
            
            # 3. Count rows in each table
            print("📈 ROW COUNTS BY TABLE")
            print("-" * 80)
            table_data = {}
            for table in tables:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                table_data[table] = count
                status = "✅" if count > 0 else "⚪"
                print(f"{status} {table:30} {count:>10,} rows")
            print()
            
            # 4. Analyze critical tables
            print("🔍 CRITICAL DATA ANALYSIS")
            print("-" * 80)
            
            critical_tables = {
                'breeds': 'Breed data (required for matching)',
                'breed_images': 'Breed images (for UI)',
                'users': 'User accounts',
                'sessions': 'Chat sessions',
                'saved_results': 'Saved recommendations',
                'favorites': 'User favorites',
                'chat_messages': 'Conversation history'
            }
            
            for table_name, description in critical_tables.items():
                if table_name in table_data:
                    count = table_data[table_name]
                    if count > 0:
                        print(f"✅ {table_name:20} {count:>6} rows - {description}")
                    else:
                        print(f"⚠️  {table_name:20} {count:>6} rows - {description} (EMPTY)")
                else:
                    print(f"❌ {table_name:20}        - Table doesn't exist!")
            print()
            
            # 5. Sample breed data
            if 'breeds' in table_data and table_data['breeds'] > 0:
                print("🐕 SAMPLE BREED DATA")
                print("-" * 80)
                result = await conn.execute(text("""
                    SELECT name, size, energy_level, family_friendly 
                    FROM breeds 
                    LIMIT 10
                """))
                breeds = result.fetchall()
                print(f"Sample of {len(breeds)} breeds:")
                for breed in breeds:
                    print(f"  • {breed[0]:30} Size: {breed[1]:10} Energy: {breed[2]}/5  Family: {breed[3]}/5")
                print()
            
            # 6. Check for user data
            if 'users' in table_data and table_data['users'] > 0:
                print("👤 USER DATA SUMMARY")
                print("-" * 80)
                result = await conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(*) FILTER (WHERE is_anonymous = true) as anonymous_users,
                        COUNT(*) FILTER (WHERE is_anonymous = false) as registered_users
                    FROM users
                """))
                user_stats = result.fetchone()
                print(f"Total Users: {user_stats[0]}")
                print(f"  • Anonymous: {user_stats[1]}")
                print(f"  • Registered: {user_stats[2]}")
                print()
            
            # 7. Generate recommendations
            print("💡 RECOMMENDATIONS FOR PRODUCTION")
            print("=" * 80)
            
            must_load = []
            should_load = []
            skip = []
            
            # Determine what needs to be loaded
            if 'breeds' in table_data:
                if table_data['breeds'] > 0:
                    must_load.append(('breeds', table_data['breeds'], 'Core app functionality'))
                else:
                    print("⚠️  WARNING: No breed data found! Run populate_breeds.py first")
            
            if 'breed_images' in table_data and table_data['breed_images'] > 0:
                should_load.append(('breed_images', table_data['breed_images'], 'UI images'))
            
            # User-generated data (usually don't transfer to prod)
            if 'users' in table_data and table_data['users'] > 0:
                skip.append(('users', table_data['users'], 'Test/development data'))
            
            if 'sessions' in table_data and table_data['sessions'] > 0:
                skip.append(('sessions', table_data['sessions'], 'Test sessions'))
            
            if 'saved_results' in table_data and table_data['saved_results'] > 0:
                skip.append(('saved_results', table_data['saved_results'], 'Test results'))
            
            if 'favorites' in table_data and table_data['favorites'] > 0:
                skip.append(('favorites', table_data['favorites'], 'Test favorites'))
            
            if 'chat_messages' in table_data and table_data['chat_messages'] > 0:
                skip.append(('chat_messages', table_data['chat_messages'], 'Test conversations'))
            
            print("\n🚀 MUST LOAD TO PRODUCTION:")
            print("-" * 80)
            if must_load:
                for table, count, reason in must_load:
                    print(f"✅ {table:20} {count:>6} rows - {reason}")
                    print(f"   Command: railway run python populate_breeds.py")
            else:
                print("⚠️  No critical data to load! Ensure breeds are populated first.")
            
            print("\n📦 SHOULD CONSIDER LOADING:")
            print("-" * 80)
            if should_load:
                for table, count, reason in should_load:
                    print(f"📋 {table:20} {count:>6} rows - {reason}")
            else:
                print("None")
            
            print("\n🚫 SKIP (Development/Test Data):")
            print("-" * 80)
            if skip:
                for table, count, reason in skip:
                    print(f"⚪ {table:20} {count:>6} rows - {reason}")
            else:
                print("None - Fresh database")
            
            # 8. Export commands
            print("\n" + "=" * 80)
            print("📝 SUGGESTED WORKFLOW FOR PRODUCTION")
            print("=" * 80)
            print("""
1. Deploy to Railway:
   • Push your code to GitHub
   • Railway auto-deploys
   • Tables are created automatically on first run

2. Load breed data:
   railway run python populate_breeds.py

3. (Optional) Verify data loaded:
   railway run python scripts/verify_database.py

4. Test the API:
   • Visit: https://your-app.up.railway.app/docs
   • Try the /breeds endpoint
   • Test chat functionality

5. Monitor logs:
   railway logs --follow
            """)
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nPossible issues:")
        print("  1. Database not running: brew services start postgresql")
        print("  2. Wrong DATABASE_URL in .env")
        print("  3. Database not initialized: python scripts/init_database.py")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("\n")
    asyncio.run(analyze_database())
    print("\n")

"""
Load breed data from exported CSV files into production database.

This ensures exact data parity between local and production.
Run this on Railway after deployment.
"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.core.database import engine


async def load_from_csv():
    """Load breeds and images from CSV exports"""
    
    print("=" * 80)
    print("LOADING DATA FROM CSV TO PRODUCTION DATABASE")
    print("=" * 80)
    print()
    
    export_dir = Path("data_exports")
    breeds_file = export_dir / "breeds_export.csv"
    images_file = export_dir / "breed_images_export.csv"
    
    # Verify files exist
    if not breeds_file.exists():
        print(f"❌ Breeds file not found: {breeds_file}")
        return
    
    if not images_file.exists():
        print(f"❌ Images file not found: {images_file}")
        return
    
    try:
        async with engine.begin() as conn:
            # Check if database is empty
            result = await conn.execute(text("SELECT COUNT(*) FROM breeds"))
            existing_count = result.scalar()
            
            if existing_count > 0:
                print(f"⚠️  Database already has {existing_count} breeds")
                response = input("Clear and reload? (yes/no): ")
                if response.lower() != 'yes':
                    print("Aborted.")
                    return
                
                # Clear existing data
                print("\n🗑️  Clearing existing data...")
                await conn.execute(text("DELETE FROM breed_images"))
                await conn.execute(text("DELETE FROM breeds"))
                print("✅ Cleared")
            
            # Load breeds
            print("\n📋 Loading breeds...")
            with open(breeds_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                breeds = list(reader)
                
                for breed in breeds:
                    await conn.execute(text("""
                        INSERT INTO breeds (id, name, traits, description, created_at)
                        VALUES (:id, :name, :traits, :description, :created_at)
                    """), {
                        'id': breed['id'],
                        'name': breed['name'],
                        'traits': breed['traits'],
                        'description': breed['description'] if breed['description'] else None,
                        'created_at': breed['created_at']
                    })
            
            print(f"✅ Loaded {len(breeds)} breeds")
            
            # Load breed images
            print("\n📸 Loading breed images...")
            with open(images_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                images = list(reader)
                
                # Batch insert for performance
                batch_size = 100
                for i in range(0, len(images), batch_size):
                    batch = images[i:i+batch_size]
                    for image in batch:
                        await conn.execute(text("""
                            INSERT INTO breed_images (id, breed_id, url, image_number, breed_folder, created_at)
                            VALUES (:id, :breed_id, :url, :image_number, :breed_folder, :created_at)
                        """), {
                            'id': image['id'],
                            'breed_id': image['breed_id'],
                            'url': image['url'],
                            'image_number': int(image['image_number']),
                            'breed_folder': image['breed_folder'],
                            'created_at': image['created_at']
                        })
                    print(f"   Progress: {min(i+batch_size, len(images))}/{len(images)} images")
            
            print(f"✅ Loaded {len(images)} breed images")
            
            # Verify
            print("\n✅ VERIFICATION")
            print("=" * 80)
            result = await conn.execute(text("SELECT COUNT(*) FROM breeds"))
            breed_count = result.scalar()
            print(f"Breeds in database: {breed_count}")
            
            result = await conn.execute(text("SELECT COUNT(*) FROM breed_images"))
            image_count = result.scalar()
            print(f"Images in database: {image_count}")
            
            print("\n🎉 SUCCESS! Production database loaded.")
            print("\nNext steps:")
            print("   1. Test API: curl https://your-app.up.railway.app/api/breeds")
            print("   2. Check logs: railway logs")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print()
    asyncio.run(load_from_csv())
    print()

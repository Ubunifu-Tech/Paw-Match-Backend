"""
Export current database data to CSV files for production loading.

This ensures we load the exact data that's working in local development.
"""

import asyncio
import csv
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from dotenv import load_dotenv
load_dotenv()

from app.core.database import engine


async def export_database():
    """Export breeds and breed_images to CSV"""
    
    print("=" * 80)
    print("EXPORTING DATABASE TO CSV FILES")
    print("=" * 80)
    print()
    
    export_dir = Path("data_exports")
    export_dir.mkdir(exist_ok=True)
    
    try:
        async with engine.begin() as conn:
            # Export breeds
            print("📋 Exporting breeds...")
            result = await conn.execute(text("""
                SELECT id, name, traits, description, created_at
                FROM breeds
                ORDER BY name
            """))
            
            breeds = result.fetchall()
            breeds_file = export_dir / "breeds_export.csv"
            
            with open(breeds_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'name', 'traits', 'description', 'created_at'])
                for row in breeds:
                    writer.writerow(row)
            
            print(f"✅ Exported {len(breeds)} breeds to {breeds_file}")
            
            # Export breed_images
            print("\n📸 Exporting breed images...")
            result = await conn.execute(text("""
                SELECT id, breed_id, url, image_number, breed_folder, created_at
                FROM breed_images
                ORDER BY breed_id, image_number
            """))
            
            images = result.fetchall()
            images_file = export_dir / "breed_images_export.csv"
            
            with open(images_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'breed_id', 'url', 'image_number', 'breed_folder', 'created_at'])
                for row in images:
                    writer.writerow(row)
            
            print(f"✅ Exported {len(images)} breed images to {images_file}")
            
            # Summary
            print("\n" + "=" * 80)
            print("EXPORT SUMMARY")
            print("=" * 80)
            print(f"\n✅ Successfully exported:")
            print(f"   • {len(breeds)} breeds → {breeds_file}")
            print(f"   • {len(images)} images → {images_file}")
            
            print(f"\n📦 Files ready for production deployment!")
            print(f"\nNext steps:")
            print(f"   1. Commit these CSV files to git")
            print(f"   2. Deploy to Railway")
            print(f"   3. Run: railway run python3 load_from_csv.py")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print()
    asyncio.run(export_database())
    print()

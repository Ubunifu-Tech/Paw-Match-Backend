"""
Update database with GCS image URLs.

Run this AFTER uploading images to GCP Storage.

Usage:
    python update_db_with_gcs.py
"""

import asyncio
import json
from pathlib import Path
from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal
from app.db.models import Breed, BreedImage
import uuid

async def update_database_with_gcs_urls():
    """Update database with GCS URLs from metadata"""
    
    # Use the metadata from prepare_for_gcp.py
    metadata_file = Path("upload_images/metadata.json")
    
    if not metadata_file.exists():
        print(f"❌ Metadata file not found: {metadata_file}")
        print(f"   Make sure you've run prepare_for_gcp.py first!")
        return
    
    print(f"📄 Loading metadata...")
    metadata = json.loads(metadata_file.read_text())
    
    async with AsyncSessionLocal() as db:
        print(f"\n🔄 Updating database with GCS URLs...")
        
        updated_breeds = 0
        total_images = 0
        
        for breed_data in metadata['breeds']:
            if breed_data['status'] != 'ready':
                continue
            
            breed_name = breed_data['breed_name']
            
            # Find breed in database
            result = await db.execute(
                select(Breed).where(Breed.name == breed_name)
            )
            breed = result.scalar_one_or_none()
            
            if not breed:
                print(f"⚠️  Breed not found in DB: {breed_name}")
                continue
            
            # Delete existing images for this breed
            await db.execute(
                delete(BreedImage).where(BreedImage.breed_id == breed.id)
            )
            
            # Add new images with GCS URLs
            for idx, img_info in enumerate(breed_data['images'], 1):
                if 'gcs_url' not in img_info:
                    continue
                
                breed_image = BreedImage(
                    id=uuid.uuid4(),
                    breed_id=breed.id,
                    url=img_info['gcs_url'],
                    image_number=idx,
                    breed_folder=breed_data['safe_folder']
                )
                db.add(breed_image)
                total_images += 1
            
            updated_breeds += 1
            
            # Commit every 20 breeds
            if updated_breeds % 20 == 0:
                await db.commit()
                print(f"  ✓ Updated {updated_breeds} breeds...")
        
        # Final commit
        await db.commit()
        
        print(f"\n✅ Database updated!")
        print(f"   Breeds updated: {updated_breeds}")
        print(f"   Total images: {total_images}")
        print(f"\n🎉 All images now point to GCS!")

if __name__ == "__main__":
    asyncio.run(update_database_with_gcs_urls())

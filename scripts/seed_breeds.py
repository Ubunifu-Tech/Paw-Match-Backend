"""
Seed Breeds Script

Populates the database with all breed data and image URLs from the dataset.

Usage:
    python scripts/seed_breeds.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.db.models import Breed, BreedImage
from app.services.breed_loader import BreedDataLoader
from app.services.image_service import ImageService


async def seed_breeds():
    """Seed database with all breed data and images."""
    
    print("🌱 Seeding breed data into database...")
    print("=" * 60)
    
    # Initialize services
    breed_loader = BreedDataLoader()
    image_service = ImageService()
    
    async with AsyncSessionLocal() as db:
        # Check if data already exists
        result = await db.execute(select(Breed))
        existing_breeds = result.scalars().all()
        
        if existing_breeds:
            print(f"⚠️  Found {len(existing_breeds)} existing breeds in database")
            response = input("Do you want to clear and reseed? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Seeding cancelled")
                return
            
            # Delete existing data
            for breed in existing_breeds:
                await db.delete(breed)
            await db.commit()
            print("🗑️  Cleared existing data")
        
        # Get all breeds
        all_breeds = breed_loader.get_all_breeds()
        print(f"\n📚 Loading {len(all_breeds)} breeds...")
        
        breeds_created = 0
        images_created = 0
        
        for breed_name in all_breeds:
            try:
                # Get breed traits
                traits = breed_loader.get_breed_traits(breed_name)
                
                # Create breed record
                breed = Breed(
                    name=breed_name,
                    traits=traits.model_dump(),
                    description=f"{breed_name} - {traits.coat_type} coat, {traits.coat_length} length"
                )
                db.add(breed)
                await db.flush()  # Get the breed ID
                
                # Get images for this breed
                images = image_service.get_breed_images(breed_name, count=35)
                
                # Create image records
                for img in images:
                    breed_image = BreedImage(
                        breed_id=breed.id,
                        url=img['url'],
                        image_number=img.get('image_number', 1),
                        breed_folder=img.get('breed_folder', breed_name.replace(' ', '_'))
                    )
                    db.add(breed_image)
                    images_created += 1
                
                breeds_created += 1
                
                if breeds_created % 20 == 0:
                    print(f"  ✓ Processed {breeds_created}/{len(all_breeds)} breeds...")
                    await db.commit()
                
            except Exception as e:
                print(f"  ❌ Error processing {breed_name}: {e}")
                continue
        
        # Final commit
        await db.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ Seeding complete!")
        print(f"   Breeds created: {breeds_created}")
        print(f"   Images created: {images_created}")
        print(f"   Average images per breed: {images_created / breeds_created:.1f}")


async def verify_data():
    """Verify the seeded data."""
    
    print("\n🔍 Verifying seeded data...")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        # Count breeds
        result = await db.execute(select(Breed))
        breeds = result.scalars().all()
        print(f"✅ Total breeds: {len(breeds)}")
        
        # Count images
        result = await db.execute(select(BreedImage))
        images = result.scalars().all()
        print(f"✅ Total images: {len(images)}")
        
        # Show sample data
        if breeds:
            sample_breed = breeds[0]
            print(f"\n📋 Sample Breed: {sample_breed.name}")
            print(f"   Traits: {len(sample_breed.traits)} attributes")
            print(f"   Images: {len(sample_breed.images)} images")
            
            if sample_breed.images:
                print(f"   Sample URL: {sample_breed.images[0].url[:80]}...")


async def main():
    """Main function to run seeding and verification."""
    await seed_breeds()
    await verify_data()


if __name__ == "__main__":
    print("🐕 Dog Breed Database Seeder")
    print("=" * 60)
    
    asyncio.run(main())
    
    print("\n✅ All done!")

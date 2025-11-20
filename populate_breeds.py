"""
Populate database with breed data and images from CSV and GitHub.

This script:
1. Reads breed traits from CSV
2. Fetches actual image URLs from GitHub API
3. Populates the database with breeds and images

Run once to set up production data.
"""

import asyncio
import pandas as pd
import httpx
from pathlib import Path
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.db.models import Breed, BreedImage
import uuid

async def fetch_github_images(breed_folder: str, max_images: int = 35) -> list:
    """Fetch actual image URLs from GitHub repo"""
    base_url = "https://api.github.com/repos/maartenvandenbroeck/Dog-Breeds-Dataset/contents"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/{breed_folder}", timeout=10.0)
            if response.status_code == 200:
                files = response.json()
                # Filter for image files
                images = [
                    f["download_url"] 
                    for f in files 
                    if f["name"].lower().endswith(('.jpg', '.jpeg', '.png'))
                ][:max_images]
                return images
            else:
                print(f"  ⚠️  GitHub API returned {response.status_code} for {breed_folder}")
                return []
    except Exception as e:
        print(f"  ⚠️  Error fetching images for {breed_folder}: {e}")
        return []

def normalize_breed_to_folder(breed_name: str) -> str:
    """Convert breed name to GitHub folder format"""
    # Handle parentheses: "Retrievers (Labrador)" -> "Labrador Retriever"
    if '(' in breed_name:
        import re
        match = re.search(r'\(([^)]+)\)', breed_name)
        if match:
            inner = match.group(1)
            outer = breed_name.replace(f'({inner})', '').strip()
            breed_name = f"{inner} {outer}".strip()
    
    # Remove trailing 's'
    breed_name = breed_name.rstrip('s')
    
    # Convert to lowercase
    breed_name = breed_name.lower()
    
    # Replace non-breaking spaces
    breed_name = breed_name.replace('\u00a0', ' ')
    
    # Normalize spaces
    import re
    breed_name = re.sub(r'\s+', ' ', breed_name).strip()
    
    # Add " dog" suffix
    if not breed_name.endswith(' dog'):
        breed_name = f"{breed_name} dog"
    
    return breed_name

async def populate_database():
    """Main function to populate database"""
    print("🐕 Starting database population...")
    
    # Load CSV data
    csv_path = Path("app/data/breed_traits.csv")
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    print(f"✓ Loaded {len(df)} breeds from CSV")
    
    async with AsyncSessionLocal() as db:
        # Check if already populated
        result = await db.execute(select(Breed))
        existing_breeds = result.scalars().all()
        
        if len(existing_breeds) > 10:
            print(f"⚠️  Database already has {len(existing_breeds)} breeds")
            response = input("Do you want to re-populate? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborted.")
                return
            
            # Clear existing data
            print("Clearing existing data...")
            for breed in existing_breeds:
                await db.delete(breed)
            await db.commit()
        
        # Process each breed
        total = len(df)
        for idx, row in df.iterrows():
            breed_name = row['Breed']
            print(f"\n[{idx+1}/{total}] Processing: {breed_name}")
            
            # Create breed record
            breed = Breed(
                id=uuid.uuid4(),
                name=breed_name,
                traits={
                    'breed': breed_name,
                    'affectionate_with_family': int(row['Affectionate With Family']),
                    'good_with_young_children': int(row['Good With Young Children']),
                    'good_with_other_dogs': int(row['Good With Other Dogs']),
                    'shedding_level': int(row['Shedding Level']),
                    'coat_grooming_frequency': int(row['Coat Grooming Frequency']),
                    'drooling_level': int(row['Drooling Level']),
                    'coat_type': row['Coat Type'],
                    'coat_length': row['Coat Length'],
                    'openness_to_strangers': int(row['Openness To Strangers']),
                    'playfulness_level': int(row['Playfulness Level']),
                    'watchdog_protective_nature': int(row['Watchdog/Protective Nature']),
                    'adaptability_level': int(row['Adaptability Level']),
                    'trainability_level': int(row['Trainability Level']),
                    'energy_level': int(row['Energy Level']),
                    'barking_level': int(row['Barking Level']),
                    'mental_stimulation_needs': int(row['Mental Stimulation Needs'])
                }
            )
            db.add(breed)
            
            # Fetch images from GitHub
            folder_name = normalize_breed_to_folder(breed_name)
            print(f"  Fetching images from: {folder_name}")
            
            image_urls = await fetch_github_images(folder_name, max_images=10)
            
            if image_urls:
                print(f"  ✓ Found {len(image_urls)} images")
                for img_num, url in enumerate(image_urls, 1):
                    breed_image = BreedImage(
                        id=uuid.uuid4(),
                        breed_id=breed.id,
                        url=url,
                        image_number=img_num,
                        breed_folder=folder_name
                    )
                    db.add(breed_image)
            else:
                print(f"  ⚠️  No images found, using placeholders")
                # Add placeholder images
                for img_num in range(1, 6):
                    breed_image = BreedImage(
                        id=uuid.uuid4(),
                        breed_id=breed.id,
                        url=f"https://placedog.net/500/500?id={hash(breed_name + str(img_num)) % 1000}",
                        image_number=img_num,
                        breed_folder=folder_name
                    )
                    db.add(breed_image)
            
            # Commit every 10 breeds to avoid memory issues
            if (idx + 1) % 10 == 0:
                await db.commit()
                print(f"\n✓ Committed {idx + 1} breeds to database")
        
        # Final commit
        await db.commit()
        print(f"\n✅ Successfully populated database with {total} breeds!")
        
        # Verify
        result = await db.execute(select(Breed))
        breeds = result.scalars().all()
        
        result = await db.execute(select(BreedImage))
        images = result.scalars().all()
        
        print(f"\n📊 Final counts:")
        print(f"   Breeds: {len(breeds)}")
        print(f"   Images: {len(images)}")

if __name__ == "__main__":
    asyncio.run(populate_database())

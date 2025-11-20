"""
Download all dog breed images from GitHub dataset.

This script:
1. Reads breed names from CSV
2. Downloads images from GitHub repo
3. Organizes them in proper folder structure
4. Prepares for GCP Storage upload

Run: python download_images.py
"""

import asyncio
import httpx
import pandas as pd
from pathlib import Path
import re
from tqdm import tqdm
import json

# Configuration
GITHUB_BASE = "https://api.github.com/repos/maartenvandenbroeck/Dog-Breeds-Dataset/contents"
OUTPUT_DIR = Path("downloaded_images")
CSV_PATH = Path("app/data/breed_traits.csv")
METADATA_FILE = OUTPUT_DIR / "metadata.json"

def normalize_breed_to_folder(breed_name: str) -> str:
    """Convert breed name to GitHub folder format"""
    # CRITICAL: Replace non-breaking spaces FIRST
    breed_name = breed_name.replace('\u00a0', ' ').replace('\xa0', ' ')
    
    # Handle parentheses: "Retrievers (Labrador)" -> "Labrador Retriever"
    if '(' in breed_name:
        match = re.search(r'\(([^)]+)\)', breed_name)
        if match:
            inner = match.group(1)
            outer = breed_name.replace(f'({inner})', '').strip()
            breed_name = f"{inner} {outer}".strip()
    
    # Remove trailing 's'
    breed_name = breed_name.rstrip('s')
    
    # Convert to lowercase
    breed_name = breed_name.lower()
    
    # Normalize multiple spaces to single space
    breed_name = re.sub(r'\s+', ' ', breed_name).strip()
    
    # Add " dog" suffix
    if not breed_name.endswith(' dog'):
        breed_name = f"{breed_name} dog"
    
    return breed_name

def sanitize_filename(breed_name: str) -> str:
    """Create safe folder name for local storage"""
    # Replace special characters with underscores
    safe_name = re.sub(r'[^\w\s-]', '', breed_name)
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    return safe_name.lower()

async def fetch_breed_images(client: httpx.AsyncClient, breed_name: str, github_folder: str) -> dict:
    """Fetch all image URLs for a breed from GitHub"""
    
    try:
        # Add small delay to avoid rate limiting
        await asyncio.sleep(0.2)
        
        response = await client.get(f"{GITHUB_BASE}/{github_folder}", timeout=30.0)
        
        if response.status_code == 200:
            files = response.json()
            
            # Filter for image files
            images = [
                {
                    'name': f['name'],
                    'download_url': f['download_url'],
                    'size': f['size']
                }
                for f in files 
                if f['name'].lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
            ]
            
            return {
                'breed_name': breed_name,
                'github_folder': github_folder,
                'status': 'success',
                'image_count': len(images),
                'images': images
            }
        else:
            return {
                'breed_name': breed_name,
                'github_folder': github_folder,
                'status': 'error',
                'error_code': response.status_code,
                'image_count': 0,
                'images': []
            }
            
    except Exception as e:
        return {
            'breed_name': breed_name,
            'github_folder': github_folder,
            'status': 'error',
            'error': str(e),
            'image_count': 0,
            'images': []
        }

async def download_image(client: httpx.AsyncClient, url: str, save_path: Path) -> bool:
    """Download a single image"""
    try:
        response = await client.get(url, timeout=30.0)
        if response.status_code == 200:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(response.content)
            return True
        return False
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
        return False

async def process_all_breeds():
    """Main function to download all images"""
    
    # Load breed names from CSV
    df = pd.read_csv(CSV_PATH)
    breeds = df['Breed'].tolist()
    
    print(f"🐕 Found {len(breeds)} breeds in CSV")
    print(f"📁 Output directory: {OUTPUT_DIR.absolute()}")
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Check for existing downloads
    existing_metadata = {}
    if METADATA_FILE.exists():
        print(f"📄 Found existing metadata, checking for already downloaded breeds...")
        existing = json.loads(METADATA_FILE.read_text())
        existing_metadata = {b['breed_name']: b for b in existing.get('breeds', [])}
        already_downloaded = sum(1 for b in existing_metadata.values() if b['status'] == 'downloaded')
        print(f"   Already downloaded: {already_downloaded} breeds")
        print(f"   Will skip these and download the rest...")
    
    # Collect metadata
    metadata = {
        'total_breeds': len(breeds),
        'breeds': []
    }
    
    async with httpx.AsyncClient() as client:
        # Step 1: Fetch all image URLs
        print("\n📋 Step 1: Fetching image URLs from GitHub...")
        
        tasks = []
        breeds_to_fetch = []
        
        for breed_name in breeds:
            # Check if already downloaded
            if breed_name in existing_metadata and existing_metadata[breed_name]['status'] == 'downloaded':
                # Skip, will use existing data
                continue
            
            github_folder = normalize_breed_to_folder(breed_name)
            tasks.append(fetch_breed_images(client, breed_name, github_folder))
            breeds_to_fetch.append(breed_name)
        
        print(f"   Fetching {len(tasks)} new breeds (skipping {len(existing_metadata)} already downloaded)...")
        
        # Fetch with progress bar
        results = []
        if tasks:
            for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching"):
                result = await task
                results.append(result)
        
        # Add existing downloaded breeds to results
        for breed_name, breed_data in existing_metadata.items():
            if breed_data['status'] == 'downloaded':
                results.append(breed_data)
        
        # Step 2: Download images
        print("\n⬇️  Step 2: Downloading images...")
        
        total_images = sum(r['image_count'] for r in results if r['status'] == 'success')
        print(f"   Found {total_images} images to download")
        
        successful_downloads = 0
        failed_downloads = 0
        
        for breed_data in tqdm(results, desc="Downloading breeds"):
            # If already downloaded, skip but add to metadata
            if breed_data.get('status') == 'downloaded':
                metadata['breeds'].append(breed_data)
                successful_downloads += len(breed_data.get('images', []))
                continue
            
            if breed_data['status'] != 'success' or not breed_data['images']:
                metadata['breeds'].append({
                    'breed_name': breed_data['breed_name'],
                    'status': 'no_images',
                    'image_count': 0
                })
                continue
            
            breed_name = breed_data['breed_name']
            safe_folder = sanitize_filename(breed_name)
            breed_folder = OUTPUT_DIR / safe_folder
            
            downloaded_images = []
            
            for idx, img_info in enumerate(breed_data['images'], 1):
                # Create standardized filename
                file_ext = Path(img_info['name']).suffix
                new_filename = f"{safe_folder}_{idx:03d}{file_ext}"
                save_path = breed_folder / new_filename
                
                success = await download_image(client, img_info['download_url'], save_path)
                
                if success:
                    successful_downloads += 1
                    downloaded_images.append({
                        'original_name': img_info['name'],
                        'new_name': new_filename,
                        'local_path': str(save_path.relative_to(OUTPUT_DIR)),
                        'size': img_info['size']
                    })
                else:
                    failed_downloads += 1
            
            metadata['breeds'].append({
                'breed_name': breed_name,
                'safe_folder': safe_folder,
                'github_folder': breed_data['github_folder'],
                'status': 'downloaded',
                'image_count': len(downloaded_images),
                'images': downloaded_images
            })
        
        # Save metadata
        metadata['total_images_downloaded'] = successful_downloads
        metadata['failed_downloads'] = failed_downloads
        
        METADATA_FILE.write_text(json.dumps(metadata, indent=2))
        
        # Summary
        print(f"\n✅ Download Complete!")
        print(f"   Total images downloaded: {successful_downloads}")
        print(f"   Failed downloads: {failed_downloads}")
        print(f"   Breeds with images: {sum(1 for b in metadata['breeds'] if b['status'] == 'downloaded')}")
        print(f"   Breeds without images: {sum(1 for b in metadata['breeds'] if b['status'] == 'no_images')}")
        print(f"\n📄 Metadata saved to: {METADATA_FILE}")
        print(f"\n📦 Next step: Upload {OUTPUT_DIR} to GCP Storage bucket")

if __name__ == "__main__":
    asyncio.run(process_all_breeds())

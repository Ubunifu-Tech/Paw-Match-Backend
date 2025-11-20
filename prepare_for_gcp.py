"""
Prepare images from downloaded GitHub repo for GCP upload.

This script:
1. Reads breed names from CSV
2. Finds matching folders in the downloaded repo
3. Copies and renames images to upload_images/ folder
4. Creates metadata with GCS URLs for bucket: dawg-match

Usage:
    python prepare_for_gcp.py /path/to/Dog-Breeds-Dataset-master
"""

import pandas as pd
import shutil
import json
import sys
from pathlib import Path
import re
from tqdm import tqdm

# Configuration
CSV_PATH = Path("app/data/breed_traits.csv")
OUTPUT_DIR = Path("upload_images")
BUCKET_NAME = "dawg-match"
METADATA_FILE = OUTPUT_DIR / "metadata.json"

def normalize_breed_name(breed_name: str) -> str:
    """Normalize breed name for folder matching"""
    # Replace non-breaking spaces
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
    
    # Normalize spaces
    breed_name = re.sub(r'\s+', ' ', breed_name).strip()
    
    return breed_name

def sanitize_folder_name(name: str) -> str:
    """Create safe folder name"""
    name = name.lower()
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name)
    return name

def find_breed_folder(repo_path: Path, breed_name: str) -> Path:
    """Find the matching folder in the repo"""
    normalized = normalize_breed_name(breed_name)
    
    # Try different variations
    variations = [
        normalized,
        normalized.lower(),
        normalized.title(),
        f"{normalized} dog",
        f"{normalized.lower()} dog",
    ]
    
    for variation in variations:
        # Try exact match
        folder = repo_path / variation
        if folder.exists() and folder.is_dir():
            return folder
        
        # Try case-insensitive search
        for item in repo_path.iterdir():
            if item.is_dir() and item.name.lower() == variation.lower():
                return item
    
    return None

def process_all_breeds(repo_path):
    """Main function to prepare images"""
    
    # Load breeds from CSV
    df = pd.read_csv(CSV_PATH)
    breeds = df['Breed'].tolist()
    
    print(f"🐕 Processing {len(breeds)} breeds from CSV")
    print(f"📂 Source: {repo_path}")
    print(f"📁 Output: {OUTPUT_DIR.absolute()}")
    print(f"☁️  Bucket: gs://{BUCKET_NAME}/breed_images/")
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Metadata
    metadata = {
        'bucket_name': BUCKET_NAME,
        'total_breeds': len(breeds),
        'breeds': []
    }
    
    successful_breeds = 0
    total_images = 0
    
    print(f"\n📋 Processing breeds...")
    
    for breed_name in tqdm(breeds, desc="Processing"):
        # Find folder in repo
        breed_folder = find_breed_folder(repo_path, breed_name)
        
        if not breed_folder:
            metadata['breeds'].append({
                'breed_name': breed_name,
                'status': 'not_found',
                'image_count': 0
            })
            continue
        
        # Get all images
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            image_files.extend(breed_folder.glob(f'*{ext}'))
            image_files.extend(breed_folder.glob(f'*{ext.upper()}'))
        
        if not image_files:
            metadata['breeds'].append({
                'breed_name': breed_name,
                'status': 'no_images',
                'image_count': 0
            })
            continue
        
        # Create output folder
        safe_name = sanitize_folder_name(breed_name)
        output_folder = OUTPUT_DIR / safe_name
        output_folder.mkdir(exist_ok=True)
        
        # Copy and rename images
        images_data = []
        for idx, img_file in enumerate(sorted(image_files), 1):
            # New filename
            ext = img_file.suffix.lower()
            new_filename = f"{safe_name}_{idx:03d}{ext}"
            output_path = output_folder / new_filename
            
            # Copy file
            shutil.copy2(img_file, output_path)
            
            # Generate GCS URL
            gcs_path = f"breed_images/{safe_name}/{new_filename}"
            gcs_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{gcs_path}"
            
            images_data.append({
                'original_name': img_file.name,
                'new_name': new_filename,
                'local_path': f"{safe_name}/{new_filename}",
                'gcs_path': gcs_path,
                'gcs_url': gcs_url,
                'size': img_file.stat().st_size
            })
        
        metadata['breeds'].append({
            'breed_name': breed_name,
            'safe_folder': safe_name,
            'github_folder': breed_folder.name,
            'status': 'ready',
            'image_count': len(images_data),
            'images': images_data
        })
        
        successful_breeds += 1
        total_images += len(images_data)
    
    # Save metadata
    metadata['successful_breeds'] = successful_breeds
    metadata['total_images'] = total_images
    
    METADATA_FILE.write_text(json.dumps(metadata, indent=2))
    
    # Summary
    print(f"\n✅ Processing Complete!")
    print(f"   Breeds processed: {successful_breeds}/{len(breeds)}")
    print(f"   Total images: {total_images}")
    print(f"   Output folder: {OUTPUT_DIR.absolute()}")
    print(f"   Metadata: {METADATA_FILE}")
    
    # Show folder size
    total_size = sum(f.stat().st_size for f in OUTPUT_DIR.rglob('*') if f.is_file())
    size_mb = total_size / (1024 * 1024)
    print(f"   Total size: {size_mb:.1f} MB")
    
    print(f"\n📦 Next Steps:")
    print(f"   1. Upload {OUTPUT_DIR}/ to GCS bucket: dawg-match")
    print(f"   2. Run: python update_db_with_gcs.py")
    print(f"\n💡 Upload command:")
    print(f"   gsutil -m cp -r {OUTPUT_DIR}/* gs://{BUCKET_NAME}/breed_images/")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Usage: python prepare_for_gcp.py /path/to/Dog-Breeds-Dataset-master")
        print("\nExample:")
        print("  python prepare_for_gcp.py ~/Desktop/Dog-Breeds-Dataset-master")
        sys.exit(1)
    
    repo_path = Path(sys.argv[1])
    
    if not repo_path.exists():
        print(f"❌ Repo not found: {repo_path}")
        print(f"   Please check the path!")
        sys.exit(1)
    
    process_all_breeds(repo_path)

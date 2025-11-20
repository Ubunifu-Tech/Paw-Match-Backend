"""
Create a clean upload folder with only the necessary image files.
Removes metadata.json and any extra files - just images ready for GCP.

Usage:
    python create_clean_upload.py
"""

import json
import shutil
from pathlib import Path
from tqdm import tqdm

SOURCE_DIR = Path("upload_images")
CLEAN_DIR = Path("gcp_upload")
METADATA_FILE = SOURCE_DIR / "metadata.json"

def create_clean_upload():
    """Create clean folder with only images"""
    
    if not SOURCE_DIR.exists():
        print(f"❌ Source folder not found: {SOURCE_DIR}")
        print(f"   Run prepare_for_gcp.py first!")
        return
    
    if not METADATA_FILE.exists():
        print(f"❌ Metadata not found: {METADATA_FILE}")
        return
    
    # Load metadata
    metadata = json.loads(METADATA_FILE.read_text())
    
    print(f"🧹 Creating clean upload folder...")
    print(f"📂 Source: {SOURCE_DIR}")
    print(f"📁 Output: {CLEAN_DIR}")
    
    # Remove old clean directory if exists
    if CLEAN_DIR.exists():
        print(f"   Removing old {CLEAN_DIR}...")
        shutil.rmtree(CLEAN_DIR)
    
    # Create new clean directory
    CLEAN_DIR.mkdir()
    
    total_images = 0
    total_breeds = 0
    
    # Copy only image files
    for breed_data in tqdm(metadata['breeds'], desc="Copying"):
        if breed_data['status'] != 'ready':
            continue
        
        safe_folder = breed_data['safe_folder']
        source_breed_folder = SOURCE_DIR / safe_folder
        
        if not source_breed_folder.exists():
            continue
        
        # Create breed folder in clean directory
        clean_breed_folder = CLEAN_DIR / safe_folder
        clean_breed_folder.mkdir()
        
        # Copy only image files
        for img_data in breed_data['images']:
            source_file = SOURCE_DIR / img_data['local_path']
            dest_file = CLEAN_DIR / img_data['local_path']
            
            if source_file.exists():
                shutil.copy2(source_file, dest_file)
                total_images += 1
        
        total_breeds += 1
    
    # Calculate size
    total_size = sum(f.stat().st_size for f in CLEAN_DIR.rglob('*') if f.is_file())
    size_mb = total_size / (1024 * 1024)
    
    print(f"\n✅ Clean upload folder created!")
    print(f"   Breeds: {total_breeds}")
    print(f"   Images: {total_images}")
    print(f"   Size: {size_mb:.1f} MB")
    print(f"   Location: {CLEAN_DIR.absolute()}")
    
    # Show structure
    print(f"\n📋 Folder structure:")
    folders = sorted([d for d in CLEAN_DIR.iterdir() if d.is_dir()])
    for folder in folders[:5]:
        image_count = len(list(folder.glob('*.jpg'))) + len(list(folder.glob('*.png')))
        print(f"   {folder.name}/ ({image_count} images)")
    if len(folders) > 5:
        print(f"   ... and {len(folders) - 5} more breed folders")
    
    print(f"\n📦 Ready to upload!")
    print(f"   gsutil -m cp -r {CLEAN_DIR}/* gs://dawg-match/breed_images/")
    print(f"\n   Or drag-and-drop {CLEAN_DIR}/ to GCP Console")

if __name__ == "__main__":
    create_clean_upload()

"""
Rename all downloaded image files to remove spaces.
Makes them safe for manual upload to GCP.

Usage:
    python rename_files.py
"""

import json
from pathlib import Path
import shutil

def sanitize_filename(name: str) -> str:
    """Remove spaces and special characters from filename"""
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Replace other problematic characters
    name = name.replace('(', '').replace(')', '')
    name = name.replace("'", '').replace('"', '')
    # Remove multiple underscores
    while '__' in name:
        name = name.replace('__', '_')
    return name.lower()

def rename_all_files(source_dir: Path):
    """Rename all files in the directory structure"""
    
    print(f"📁 Processing directory: {source_dir}")
    
    renamed_count = 0
    skipped_count = 0
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    all_files = []
    
    for ext in image_extensions:
        all_files.extend(source_dir.rglob(f'*{ext}'))
    
    print(f"📊 Found {len(all_files)} image files")
    print(f"\n🔄 Renaming files...")
    
    for file_path in all_files:
        # Get new filename
        new_name = sanitize_filename(file_path.name)
        
        if new_name == file_path.name:
            skipped_count += 1
            continue
        
        # Get new path
        new_path = file_path.parent / new_name
        
        # Rename
        try:
            file_path.rename(new_path)
            renamed_count += 1
            
            if renamed_count <= 5:  # Show first 5 examples
                print(f"  ✓ {file_path.name} → {new_name}")
        except Exception as e:
            print(f"  ❌ Failed to rename {file_path.name}: {e}")
    
    # Also rename directories
    print(f"\n📂 Renaming directories...")
    dir_renamed = 0
    
    # Get all subdirectories (sorted by depth, deepest first)
    all_dirs = sorted([d for d in source_dir.rglob('*') if d.is_dir()], 
                     key=lambda x: len(x.parts), reverse=True)
    
    for dir_path in all_dirs:
        new_name = sanitize_filename(dir_path.name)
        
        if new_name == dir_path.name:
            continue
        
        new_path = dir_path.parent / new_name
        
        try:
            dir_path.rename(new_path)
            dir_renamed += 1
            
            if dir_renamed <= 5:  # Show first 5 examples
                print(f"  ✓ {dir_path.name}/ → {new_name}/")
        except Exception as e:
            print(f"  ❌ Failed to rename {dir_path.name}: {e}")
    
    print(f"\n✅ Complete!")
    print(f"   Files renamed: {renamed_count}")
    print(f"   Files skipped: {skipped_count}")
    print(f"   Directories renamed: {dir_renamed}")
    print(f"\n📦 Ready for manual upload!")
    print(f"   Directory: {source_dir.absolute()}")

def main():
    source_dir = Path("downloaded_images")
    
    if not source_dir.exists():
        print(f"❌ Directory not found: {source_dir}")
        print(f"   Make sure download_images.py has completed.")
        return
    
    rename_all_files(source_dir)

if __name__ == "__main__":
    main()

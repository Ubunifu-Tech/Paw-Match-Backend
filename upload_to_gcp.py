"""
Upload downloaded images to GCP Storage.

Prerequisites:
1. Install: pip install google-cloud-storage
2. Set up GCP credentials: 
   - Create service account in GCP Console
   - Download JSON key
   - Set: export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
3. Create a GCP Storage bucket

Usage:
    python upload_to_gcp.py --bucket YOUR_BUCKET_NAME
"""

import argparse
import json
from pathlib import Path
from google.cloud import storage
from tqdm import tqdm

def upload_to_gcs(bucket_name: str, source_dir: Path, metadata_file: Path):
    """Upload all images to GCP Storage bucket"""
    
    # Initialize GCS client
    print(f"🔧 Initializing GCP Storage client...")
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    # Load metadata
    print(f"📄 Loading metadata from {metadata_file}...")
    metadata = json.loads(metadata_file.read_text())
    
    # Prepare upload list
    files_to_upload = []
    for breed_data in metadata['breeds']:
        if breed_data['status'] == 'downloaded':
            for img_info in breed_data['images']:
                local_path = source_dir / img_info['local_path']
                # GCS path: breed_images/breed_folder/filename
                gcs_path = f"breed_images/{img_info['local_path']}"
                files_to_upload.append((local_path, gcs_path))
    
    print(f"\n📦 Uploading {len(files_to_upload)} images to gs://{bucket_name}/...")
    
    # Upload with progress bar
    uploaded_count = 0
    failed_count = 0
    uploaded_urls = {}
    
    for local_path, gcs_path in tqdm(files_to_upload, desc="Uploading"):
        try:
            blob = bucket.blob(gcs_path)
            blob.upload_from_filename(str(local_path))
            
            # Make publicly readable (optional)
            blob.make_public()
            
            uploaded_count += 1
            uploaded_urls[gcs_path] = blob.public_url
            
        except Exception as e:
            print(f"\n❌ Failed to upload {local_path}: {e}")
            failed_count += 1
    
    # Update metadata with GCS URLs
    for breed_data in metadata['breeds']:
        if breed_data['status'] == 'downloaded':
            for img_info in breed_data['images']:
                gcs_path = f"breed_images/{img_info['local_path']}"
                if gcs_path in uploaded_urls:
                    img_info['gcs_url'] = uploaded_urls[gcs_path]
    
    # Save updated metadata
    updated_metadata_file = source_dir / "metadata_with_gcs_urls.json"
    updated_metadata_file.write_text(json.dumps(metadata, indent=2))
    
    print(f"\n✅ Upload Complete!")
    print(f"   Uploaded: {uploaded_count} images")
    print(f"   Failed: {failed_count} images")
    print(f"   Bucket: gs://{bucket_name}/breed_images/")
    print(f"   Updated metadata: {updated_metadata_file}")
    print(f"\n🔗 Example URL: {list(uploaded_urls.values())[0] if uploaded_urls else 'N/A'}")

def main():
    parser = argparse.ArgumentParser(description='Upload dog breed images to GCP Storage')
    parser.add_argument('--bucket', required=True, help='GCP Storage bucket name')
    parser.add_argument('--source-dir', default='downloaded_images', help='Local images directory')
    
    args = parser.parse_args()
    
    source_dir = Path(args.source_dir)
    metadata_file = source_dir / "metadata.json"
    
    if not source_dir.exists():
        print(f"❌ Source directory not found: {source_dir}")
        print(f"   Run download_images.py first!")
        return
    
    if not metadata_file.exists():
        print(f"❌ Metadata file not found: {metadata_file}")
        return
    
    upload_to_gcs(args.bucket, source_dir, metadata_file)

if __name__ == "__main__":
    main()

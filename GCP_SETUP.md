# 🐕 GCP Storage Setup for Dog Breed Images

Complete guide to download, organize, and host all dog breed images on Google Cloud Storage.

## 📋 Prerequisites

1. **GCP Account** with billing enabled
2. **Python packages**: `google-cloud-storage` 
3. **GCP CLI** (optional but recommended): `gcloud`

## 🚀 Step-by-Step Guide

### Step 1: Download Images from GitHub

```bash
# This downloads ~1000+ images from the GitHub dataset
python download_images.py
```

**Output:**
- Directory: `downloaded_images/`
- Metadata: `downloaded_images/metadata.json`
- Organized structure: `downloaded_images/breed_folder/breed_001.jpg`

### Step 2: Set Up GCP Storage Bucket

#### Option A: Using GCP Console (Web UI)

1. Go to [GCP Console](https://console.cloud.google.com/)
2. Navigate to **Cloud Storage** → **Buckets**
3. Click **CREATE BUCKET**
4. Choose:
   - **Name**: `pawmatch-dog-images` (must be globally unique)
   - **Location**: Choose closest to your users (e.g., `us-central1`)
   - **Storage class**: `Standard`
   - **Access control**: `Fine-grained`
   - **Public access**: Enable "Enforce public access prevention" = OFF (for public URLs)
5. Click **CREATE**

#### Option B: Using gcloud CLI

```bash
# Create bucket
gsutil mb -l us-central1 gs://pawmatch-dog-images

# Make bucket publicly readable (optional)
gsutil iam ch allUsers:objectViewer gs://pawmatch-dog-images
```

### Step 3: Create Service Account & Download Credentials

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **CREATE SERVICE ACCOUNT**
   - Name: `pawmatch-storage-admin`
   - Role: **Storage Admin** (or **Storage Object Admin**)
3. Click **DONE**
4. Click on the service account
5. Go to **KEYS** tab → **ADD KEY** → **Create new key** → **JSON**
6. Save the downloaded JSON file as `gcp-credentials.json`

### Step 4: Set Up Environment

```bash
# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcp-credentials.json"

# Or add to your .env file
echo "GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-credentials.json" >> .env
```

### Step 5: Install GCP Python Library

```bash
pip install google-cloud-storage
```

### Step 6: Upload Images to GCS

```bash
python upload_to_gcp.py --bucket pawmatch-dog-images
```

**This will:**
- Upload all images to `gs://pawmatch-dog-images/breed_images/`
- Make them publicly accessible
- Generate `metadata_with_gcs_urls.json` with all public URLs

**Output URLs will look like:**
```
https://storage.googleapis.com/pawmatch-dog-images/breed_images/labrador_retriever/labrador_retriever_001.jpg
```

### Step 7: Update Database with GCS URLs

```bash
python update_db_with_gcs.py
```

**This will:**
- Read the metadata with GCS URLs
- Update PostgreSQL database
- Replace all image URLs with GCS URLs

### Step 8: Verify

```bash
# Test the image service
python -c "
import asyncio
from app.services.image_service import ImageService

async def test():
    service = ImageService()
    images = await service.get_breed_images('Retrievers (Labrador)', count=3)
    for img in images:
        print(img['url'])

asyncio.run(test())
"
```

## 📊 Expected Costs

**GCS Storage (Standard)**:
- ~1000 images × ~200KB avg = ~200MB
- Storage: $0.020 per GB/month = **~$0.004/month**
- Egress: First 1GB/month free, then $0.12/GB
- Operations: Negligible for this use case

**Estimate: <$1/month** for typical usage

## 🔒 Security Best Practices

1. **Service Account**: Use least-privilege (Storage Object Admin only)
2. **Bucket Permissions**: Consider signed URLs instead of public access for sensitive content
3. **Credentials**: Never commit `gcp-credentials.json` to git
4. **IAM**: Regularly audit service account permissions

## 🎯 Bucket Structure

```
gs://pawmatch-dog-images/
└── breed_images/
    ├── labrador_retriever/
    │   ├── labrador_retriever_001.jpg
    │   ├── labrador_retriever_002.jpg
    │   └── ...
    ├── french_bulldog/
    │   ├── french_bulldog_001.jpg
    │   └── ...
    └── ...
```

## 🔧 Troubleshooting

### "Access Denied" Error
```bash
# Ensure credentials are set
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test auth
gcloud auth application-default print-access-token
```

### "Bucket Already Exists"
```bash
# Bucket names are globally unique
# Try a different name like: pawmatch-dog-images-[your-id]
```

### Images Not Public
```bash
# Make bucket publicly readable
gsutil iam ch allUsers:objectViewer gs://your-bucket-name
```

## 🔄 Updating Images Later

To add new images or update existing ones:

```bash
# 1. Re-download (updates metadata.json)
python download_images.py

# 2. Re-upload (updates GCS)
python upload_to_gcp.py --bucket your-bucket-name

# 3. Update database
python update_db_with_gcs.py
```

## 📝 Notes

- Images are downloaded once and cached locally
- GCS URLs are permanent (don't change unless you delete/move files)
- Consider setting up CDN (Cloud CDN) for better performance at scale
- Enable versioning on bucket for backup/rollback capability

## ✅ Success Checklist

- [ ] Downloaded images from GitHub
- [ ] Created GCS bucket
- [ ] Set up service account & credentials
- [ ] Uploaded images to GCS
- [ ] Updated database with GCS URLs
- [ ] Verified images load in application
- [ ] Tested on frontend (cleared cache, new session)

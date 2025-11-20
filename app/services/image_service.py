"""ImageService - Retrieves breed images from database (GCP bucket URLs)

All images are stored in Google Cloud Storage bucket and URLs are in PostgreSQL.
No local images or external sources are used.

Author: PawMatch Team
Version: 2.0.0
"""

from typing import List, Dict
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.db.models import Breed, BreedImage


class ImageService:
    """Service for retrieving breed images from database.
    
    All image URLs point to GCP bucket: gs://dawg-match/breed_images/
    No local file access or external image sources.
    """
    
    def __init__(self):
        # GCP bucket base URL (public read access)
        self.gcp_bucket_base = "https://storage.googleapis.com/dawg-match/breed_images"
        
    
    async def get_breed_images(
        self, 
        breed_name: str, 
        count: int = 5,
        random_order: bool = False
    ) -> List[Dict[str, any]]:
        """
        Get breed images from database (GCP bucket URLs).
        
        Args:
            breed_name: Name of the breed
            count: Number of images to return
            random_order: If True, return random images; if False, return in order
            
        Returns:
            List of image dictionaries with 'url', 'alt', 'breed_folder', 'image_number'
            Returns empty list if breed not found.
        """
        # Normalize spaces (handle non-breaking spaces)
        normalized_breed_name = breed_name.replace('\xa0', ' ').replace('\u00a0', ' ')
        
        async with AsyncSessionLocal() as db:
            # Get breed ID
            breed_result = await db.execute(
                select(Breed.id).where(Breed.name == normalized_breed_name)
            )
            breed_id = breed_result.scalar_one_or_none()
            
            if not breed_id:
                # Breed not found - return empty list
                # Caller should handle this (e.g., show error or use default)
                return []
            
            # Get images from database
            query = select(BreedImage).where(BreedImage.breed_id == breed_id)
            
            # Random order or sequential
            if random_order:
                query = query.order_by(func.random())
            else:
                query = query.order_by(BreedImage.image_number)
            
            query = query.limit(count)
            
            images_result = await db.execute(query)
            db_images = images_result.scalars().all()
            
            if not db_images:
                # Breed exists but no images - return empty list
                return []
            
            # Convert to dict format
            # URLs are already full GCP bucket URLs from database
            return [{
                "url": img.url,  # Full GCP bucket URL
                "alt": f"{normalized_breed_name} - Image {img.image_number}",
                "breed_folder": img.breed_folder,
                "image_number": img.image_number
            } for img in db_images]
    
    async def get_random_breed_image(self, breed_name: str) -> Dict[str, any]:
        """
        Get a single random image for a breed.
        
        Args:
            breed_name: Name of the breed
            
        Returns:
            Single image dict or None if no images found
        """
        images = await self.get_breed_images(breed_name, count=1, random_order=True)
        return images[0] if images else None
    
    async def get_breed_image_count(self, breed_name: str) -> int:
        """
        Get total number of images available for a breed.
        
        Args:
            breed_name: Name of the breed
            
        Returns:
            Number of images available
        """
        normalized_breed_name = breed_name.replace('\xa0', ' ').replace('\u00a0', ' ')
        
        async with AsyncSessionLocal() as db:
            breed_result = await db.execute(
                select(Breed.id).where(Breed.name == normalized_breed_name)
            )
            breed_id = breed_result.scalar_one_or_none()
            
            if not breed_id:
                return 0
            
            count_result = await db.execute(
                select(func.count()).select_from(BreedImage).where(BreedImage.breed_id == breed_id)
            )
            return count_result.scalar() or 0

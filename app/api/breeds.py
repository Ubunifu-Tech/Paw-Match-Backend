"""
Breeds API Endpoints

Provides endpoints for retrieving breed information from the database.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.services.breed_service import BreedService

router = APIRouter(prefix="/breeds", tags=["breeds"])


@router.get("/")
async def get_all_breeds():
    """
    Get list of all breed names.
    
    Returns:
        dict: Dictionary with 'breeds' key containing list of breed names
        
    Example:
        >>> GET /api/breeds/
        {"breeds": ["Labrador Retriever", "Golden Retriever", ...]}
    """
    service = BreedService()
    breeds = await service.get_all_breeds()
    return {"breeds": breeds}


@router.get("/list")
async def get_breeds_list():
    """
    Get list of all breeds with basic info (name, traits, first image).
    Optimized for browse page.
    
    Returns:
        dict: Dictionary with 'breeds' array containing breed objects
        
    Example:
        >>> GET /api/breeds/list
        {
            "breeds": [
                {
                    "name": "Labrador Retriever",
                    "size": "Large",
                    "energy_level": 5,
                    "good_with_children": 5,
                    "image": "https://storage.googleapis.com/..."
                },
                ...
            ]
        }
    """
    from app.core.database import AsyncSessionLocal
    from app.db.models import Breed, BreedImage
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        # Get all breeds with their first image
        result = await db.execute(
            select(Breed).order_by(Breed.name)
        )
        breeds = result.scalars().all()
        
        breed_list = []
        for breed in breeds:
            # Get first image
            img_result = await db.execute(
                select(BreedImage.url)
                .where(BreedImage.breed_id == breed.id)
                .order_by(BreedImage.image_number)
                .limit(1)
            )
            first_image = img_result.scalar_one_or_none()
            
            breed_list.append({
                "name": breed.name,
                "energy_level": breed.traits.get("energy_level", 3),
                "good_with_children": breed.traits.get("good_with_young_children", 3),
                "good_with_other_dogs": breed.traits.get("good_with_other_dogs", 3),
                "shedding_level": breed.traits.get("shedding_level", 3),
                "grooming_needs": breed.traits.get("coat_grooming_frequency", 3),
                "trainability": breed.traits.get("trainability_level", 3),
                "image": first_image
            })
        
        return {"breeds": breed_list}


@router.get("/{breed_name:path}")
async def get_breed_details(breed_name: str):
    """
    Get detailed information for a specific breed.
    
    Args:
        breed_name (str): Name of the breed (URL encoded)
        
    Returns:
        dict: Breed details including traits and images
        
    Raises:
        HTTPException: 404 if breed not found
        
    Example:
        >>> GET /api/breeds/Labrador Retriever
        {
            "breed": "Labrador Retriever",
            "traits": {...},
            "images": [...]
        }
    """
    from urllib.parse import unquote
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Decode URL encoding and normalize spaces
    decoded_name = unquote(breed_name)
    # Replace non-breaking spaces with regular spaces
    decoded_name = decoded_name.replace('\xa0', ' ').replace('\u00a0', ' ')
    logger.info(f"Looking up breed: '{decoded_name}'")
    
    service = BreedService()
    details = await service.get_breed_details(decoded_name)
    
    if not details:
        # Try to find similar breeds for better error message
        from app.core.database import AsyncSessionLocal
        from app.db.models import Breed
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            # Search for breeds containing the search term
            result = await db.execute(
                select(Breed.name)
                .where(Breed.name.ilike(f"%{decoded_name}%"))
                .limit(5)
            )
            similar = result.scalars().all()
            
            if similar:
                logger.warning(f"Breed '{decoded_name}' not found. Similar breeds: {similar}")
                raise HTTPException(
                    status_code=404, 
                    detail=f"Breed not found: '{decoded_name}'. Did you mean: {', '.join(similar[:3])}?"
                )
        
        raise HTTPException(
            status_code=404, 
            detail=f"Breed not found: {decoded_name}"
        )
    
    return details
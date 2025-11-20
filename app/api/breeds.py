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
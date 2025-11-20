"""
Favorites API Endpoints

Provides endpoints for managing user's favorite breeds.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import AsyncSessionLocal
from app.db.models import Favorite, Breed, User
from app.core.security import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/favorites", tags=["favorites"])


class FavoriteResponse(BaseModel):
    """Response model for favorite breed."""
    breed_id: str
    breed_name: str
    image: str | None = None
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[FavoriteResponse])
async def get_user_favorites(current_user: User = Depends(get_current_user)):
    """
    Get all favorite breeds for the current user.
    
    Returns:
        List[FavoriteResponse]: List of user's favorite breeds
    """
    async with AsyncSessionLocal() as db:
        # Get user's favorites with breed info
        result = await db.execute(
            select(Favorite, Breed)
            .join(Breed, Favorite.breed_id == Breed.id)
            .where(Favorite.user_id == current_user.id)
            .order_by(Favorite.created_at.desc())
        )
        favorites = result.all()
        
        # Get first image for each breed
        from app.db.models import BreedImage
        
        response = []
        for fav, breed in favorites:
            # Get first image
            img_result = await db.execute(
                select(BreedImage.url)
                .where(BreedImage.breed_id == breed.id)
                .order_by(BreedImage.image_number)
                .limit(1)
            )
            first_image = img_result.scalar_one_or_none()
            
            response.append(FavoriteResponse(
                breed_id=str(breed.id),
                breed_name=breed.name,
                image=first_image,
                created_at=fav.created_at.isoformat()
            ))
        
        return response


@router.post("/{breed_name}")
async def add_favorite(breed_name: str, current_user: User = Depends(get_current_user)):
    """
    Add a breed to user's favorites.
    
    Args:
        breed_name (str): Name of the breed to favorite
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if breed not found, 400 if already favorited
    """
    from urllib.parse import unquote
    
    decoded_name = unquote(breed_name)
    # Replace non-breaking spaces with regular spaces
    decoded_name = decoded_name.replace('\xa0', ' ').replace('\u00a0', ' ')
    
    async with AsyncSessionLocal() as db:
        # Find breed
        result = await db.execute(
            select(Breed).where(Breed.name == decoded_name)
        )
        breed = result.scalar_one_or_none()
        
        if not breed:
            raise HTTPException(status_code=404, detail=f"Breed not found: {decoded_name}")
        
        # Check if already favorited
        existing = await db.execute(
            select(Favorite).where(
                and_(
                    Favorite.user_id == current_user.id,
                    Favorite.breed_id == breed.id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Breed already in favorites")
        
        # Add to favorites
        favorite = Favorite(
            user_id=current_user.id,
            breed_id=breed.id
        )
        db.add(favorite)
        await db.commit()
        
        return {"message": f"{breed.name} added to favorites"}


@router.delete("/{breed_name}")
async def remove_favorite(breed_name: str, current_user: User = Depends(get_current_user)):
    """
    Remove a breed from user's favorites.
    
    Args:
        breed_name (str): Name of the breed to unfavorite
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: 404 if breed or favorite not found
    """
    from urllib.parse import unquote
    
    decoded_name = unquote(breed_name)
    # Replace non-breaking spaces with regular spaces
    decoded_name = decoded_name.replace('\xa0', ' ').replace('\u00a0', ' ')
    
    async with AsyncSessionLocal() as db:
        # Find breed
        result = await db.execute(
            select(Breed).where(Breed.name == decoded_name)
        )
        breed = result.scalar_one_or_none()
        
        if not breed:
            raise HTTPException(status_code=404, detail=f"Breed not found: {decoded_name}")
        
        # Find and delete favorite
        fav_result = await db.execute(
            select(Favorite).where(
                and_(
                    Favorite.user_id == current_user.id,
                    Favorite.breed_id == breed.id
                )
            )
        )
        favorite = fav_result.scalar_one_or_none()
        
        if not favorite:
            raise HTTPException(status_code=404, detail="Favorite not found")
        
        await db.delete(favorite)
        await db.commit()
        
        return {"message": f"{breed.name} removed from favorites"}


@router.get("/check/{breed_name}")
async def check_favorite(breed_name: str, current_user: User = Depends(get_current_user)):
    """
    Check if a breed is in user's favorites.
    
    Args:
        breed_name (str): Name of the breed to check
        
    Returns:
        dict: {"is_favorite": bool}
    """
    from urllib.parse import unquote
    
    decoded_name = unquote(breed_name)
    # Replace non-breaking spaces with regular spaces
    decoded_name = decoded_name.replace('\xa0', ' ').replace('\u00a0', ' ')
    
    async with AsyncSessionLocal() as db:
        # Find breed
        result = await db.execute(
            select(Breed).where(Breed.name == decoded_name)
        )
        breed = result.scalar_one_or_none()
        
        if not breed:
            return {"is_favorite": False}
        
        # Check if favorited
        fav_result = await db.execute(
            select(Favorite).where(
                and_(
                    Favorite.user_id == current_user.id,
                    Favorite.breed_id == breed.id
                )
            )
        )
        is_favorite = fav_result.scalar_one_or_none() is not None
        
        return {"is_favorite": is_favorite}

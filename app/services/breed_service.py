"""
Breed Service

Database-backed breed data service replacing CSV-based access.

Author: PawMatch Team
Version: 1.0.0
"""

from typing import List, Optional, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Breed, BreedImage
from app.models.breed import BreedTraits, BreedDetails, BreedImage as BreedImageModel
from app.core.database import AsyncSessionLocal


class BreedService:
    """
    Database-backed breed data service.
    
    Provides methods to retrieve breed information from PostgreSQL database
    instead of CSV files. Supports caching and efficient queries.
    
    Example:
        >>> service = BreedService()
        >>> breeds = await service.get_all_breeds()
        >>> traits = await service.get_breed_traits("Labrador Retriever")
    """
    
    async def get_all_breeds(self) -> List[str]:
        """
        Get list of all breed names.
        
        Returns:
            List[str]: List of breed names
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Breed.name).order_by(Breed.name)
            )
            return [row[0] for row in result.all()]
    
    async def get_breed_by_name(self, breed_name: str) -> Optional[Breed]:
        """
        Get breed record by name.
        
        Args:
            breed_name (str): Breed name
            
        Returns:
            Optional[Breed]: Breed model or None
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Breed).where(Breed.name == breed_name)
            )
            return result.scalar_one_or_none()
    
    async def get_breed_traits(self, breed_name: str) -> Optional[BreedTraits]:
        """
        Get breed traits.
        
        Args:
            breed_name (str): Breed name
            
        Returns:
            Optional[BreedTraits]: Breed traits model or None
        """
        breed = await self.get_breed_by_name(breed_name)
        if not breed:
            return None
        
        # Convert JSONB traits to BreedTraits model
        return BreedTraits(**breed.traits)
    
    async def get_breed_details(self, breed_name: str) -> Optional[BreedDetails]:
        """
        Get complete breed details including images.
        
        Args:
            breed_name (str): Breed name
            
        Returns:
            Optional[BreedDetails]: Complete breed details or None
        """
        async with AsyncSessionLocal() as db:
            # Get breed with images
            result = await db.execute(
                select(Breed).where(Breed.name == breed_name)
            )
            breed = result.scalar_one_or_none()
            
            if not breed:
                return None
            
            # Get images
            img_result = await db.execute(
                select(BreedImage)
                .where(BreedImage.breed_id == breed.id)
                .order_by(BreedImage.image_number)
            )
            images = img_result.scalars().all()
            
            # Convert to response models
            traits = BreedTraits(**breed.traits)
            # Return just the URLs as strings
            image_urls = [img.url for img in images]
            
            return BreedDetails(
                breed=breed.name,
                traits=traits,
                images=image_urls,
                description=breed.description  # Include description from database
            )
    
    async def get_breed_images(self, breed_name: str, count: int = 5) -> List[BreedImageModel]:
        """
        Get breed images.
        
        Args:
            breed_name (str): Breed name
            count (int): Number of images to return
            
        Returns:
            List[BreedImageModel]: List of breed images
        """
        async with AsyncSessionLocal() as db:
            # Get breed ID
            breed_result = await db.execute(
                select(Breed.id).where(Breed.name == breed_name)
            )
            breed_id = breed_result.scalar_one_or_none()
            
            if not breed_id:
                return []
            
            # Get images
            result = await db.execute(
                select(BreedImage)
                .where(BreedImage.breed_id == breed_id)
                .order_by(func.random())
                .limit(count)
            )
            images = result.scalars().all()
            
            return [
                BreedImageModel(
                    url=img.url,
                    alt=f"{breed_name} - Image {img.image_number}"
                )
                for img in images
            ]
    
    async def search_breeds(self, query: str, limit: int = 10) -> List[str]:
        """
        Search breeds by name.
        
        Args:
            query (str): Search query
            limit (int): Maximum results
            
        Returns:
            List[str]: Matching breed names
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Breed.name)
                .where(Breed.name.ilike(f"%{query}%"))
                .order_by(Breed.name)
                .limit(limit)
            )
            return [row[0] for row in result.all()]
    
    async def get_breeds_by_trait(
        self, 
        trait_name: str, 
        min_value: int, 
        max_value: int = 5
    ) -> List[str]:
        """
        Get breeds filtered by trait value range.
        
        Args:
            trait_name (str): Trait name (e.g., 'energy_level')
            min_value (int): Minimum trait value
            max_value (int): Maximum trait value
            
        Returns:
            List[str]: Matching breed names
        """
        async with AsyncSessionLocal() as db:
            # Use JSONB query
            result = await db.execute(
                select(Breed.name)
                .where(
                    Breed.traits[trait_name].astext.cast(db.bind.dialect.INTEGER) >= min_value,
                    Breed.traits[trait_name].astext.cast(db.bind.dialect.INTEGER) <= max_value
                )
                .order_by(Breed.name)
            )
            return [row[0] for row in result.all()]
    
    async def get_breed_count(self) -> int:
        """
        Get total number of breeds.
        
        Returns:
            int: Total breed count
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(func.count()).select_from(Breed))
            return result.scalar()
    
    async def get_all_traits_dict(self) -> Dict[str, Dict]:
        """
        Get all breed traits as dictionary.
        
        Returns:
            Dict[str, Dict]: Dictionary mapping breed names to traits
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Breed))
            breeds = result.scalars().all()
            
            return {
                breed.name: breed.traits
                for breed in breeds
            }

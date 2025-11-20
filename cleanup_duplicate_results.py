"""
Cleanup script to remove duplicate breed results from saved_results table.

Run this once to clean up existing duplicates in the database.

Usage:
    python3 cleanup_duplicate_results.py
"""

import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.db.models.saved_result import SavedResult


async def cleanup_duplicates():
    """Remove duplicate saved results, keeping only the first occurrence per session+breed"""
    
    async with AsyncSessionLocal() as db:
        # Get all saved results ordered by session_id, breed_name, and rank
        result = await db.execute(
            select(SavedResult).order_by(
                SavedResult.session_id,
                SavedResult.breed_name,
                SavedResult.rank
            )
        )
        all_results = result.scalars().all()
        
        # Track seen (session_id, breed_name) combinations
        seen = set()
        duplicates_to_delete = []
        
        for saved_result in all_results:
            key = (saved_result.session_id, saved_result.breed_name)
            
            if key in seen:
                # This is a duplicate - mark for deletion
                duplicates_to_delete.append(saved_result)
                print(f"Found duplicate: session={saved_result.session_id}, breed={saved_result.breed_name}, rank={saved_result.rank}")
            else:
                # First occurrence - keep it
                seen.add(key)
        
        # Delete duplicates
        if duplicates_to_delete:
            print(f"\nDeleting {len(duplicates_to_delete)} duplicate records...")
            for dup in duplicates_to_delete:
                await db.delete(dup)
            
            await db.commit()
            print(f"✅ Cleanup complete! Removed {len(duplicates_to_delete)} duplicates.")
        else:
            print("✅ No duplicates found! Database is clean.")


if __name__ == "__main__":
    print("Starting duplicate cleanup...\n")
    asyncio.run(cleanup_duplicates())

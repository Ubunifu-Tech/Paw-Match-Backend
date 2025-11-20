"""
API Usage Stats Endpoints

Endpoints for users to check their API usage and limits.

Author: PawMatch Team
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.core.dependencies import get_db
from app.db.models.user import User
from app.services.usage_tracker import get_usage_tracker
from app.config.rate_limits import RateLimitConfig

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/stats")
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's API usage statistics.
    
    Returns usage for all API types with limits and remaining quota.
    """
    tracker = get_usage_tracker(db)
    stats = await tracker.get_usage_stats(current_user)
    
    return {
        "user_id": str(current_user.id),
        "usage": stats,
        "limits": RateLimitConfig.get_all_limits()
    }


@router.get("/limits")
async def get_rate_limits(current_user: User = Depends(get_current_user)):
    """Get all configured rate limits"""
    return {
        "limits": RateLimitConfig.get_all_limits(),
        "note": "Monthly limits reset on the 1st of each month"
    }

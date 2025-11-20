"""
API Usage Tracking Service

Tracks and enforces rate limits for external API calls (Gemini, etc.)

Author: PawMatch Team
"""

import logging
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.db.models.api_usage import APIUsage
from app.db.models.user import User
from app.config.rate_limits import RateLimitConfig

logger = logging.getLogger(__name__)


class UsageTracker:
    """Track and enforce API usage limits"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_and_increment(
        self,
        user: User,
        api_type: str,
        endpoint: str
    ) -> Dict:
        """
        Check if user can make API call and increment usage.
        
        Args:
            user: User making the request
            api_type: Type of API ('research', 'chat_gemini', etc.)
            endpoint: Specific endpoint being called
            
        Returns:
            Dict with usage info
            
        Raises:
            HTTPException: If user has exceeded limits
        """
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        # Get or create usage record for this month
        usage = await self._get_or_create_usage(user.id, api_type, current_month, endpoint)
        
        # Check monthly limit
        monthly_limit = RateLimitConfig.get_monthly_limit(api_type)
        if usage.count >= monthly_limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Monthly limit exceeded",
                    "api_type": api_type,
                    "limit": monthly_limit,
                    "current_usage": usage.count,
                    "reset_date": f"{current_month}-01"
                }
            )
        
        # Check daily limit (additional safety)
        today = datetime.utcnow().date()
        daily_usage = await self._get_daily_usage(user.id, api_type, today)
        daily_limit = RateLimitConfig.get_daily_limit(api_type)
        
        if daily_usage >= daily_limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Daily limit exceeded",
                    "api_type": api_type,
                    "daily_limit": daily_limit,
                    "current_usage": daily_usage,
                    "reset_time": "midnight UTC"
                }
            )
        
        # Increment usage
        usage.count += 1
        usage.last_used = datetime.utcnow()
        await self.db.commit()
        
        logger.info(
            f"API usage tracked: user_id={user.id}, api_type={api_type}, "
            f"monthly_count={usage.count}/{monthly_limit}"
        )
        
        return {
            "allowed": True,
            "monthly_usage": usage.count,
            "monthly_limit": monthly_limit,
            "remaining": monthly_limit - usage.count
        }
    
    async def _get_or_create_usage(
        self,
        user_id,
        api_type: str,
        month: str,
        endpoint: str
    ) -> APIUsage:
        """Get or create usage record"""
        
        stmt = select(APIUsage).where(
            APIUsage.user_id == user_id,
            APIUsage.api_type == api_type,
            APIUsage.month == month
        )
        
        result = await self.db.execute(stmt)
        usage = result.scalar_one_or_none()
        
        if not usage:
            usage = APIUsage(
                user_id=user_id,
                api_type=api_type,
                endpoint=endpoint,
                month=month,
                count=0
            )
            self.db.add(usage)
            await self.db.commit()
            await self.db.refresh(usage)
        
        return usage
    
    async def _get_daily_usage(self, user_id, api_type: str, date) -> int:
        """Get usage count for today"""
        
        # Get all usage records for this month
        month = date.strftime("%Y-%m")
        stmt = select(APIUsage).where(
            APIUsage.user_id == user_id,
            APIUsage.api_type == api_type,
            APIUsage.month == month
        )
        
        result = await self.db.execute(stmt)
        usage = result.scalar_one_or_none()
        
        if not usage:
            return 0
        
        # Check if last_used was today
        if usage.last_used.date() == date:
            # For simplicity, we track daily in memory
            # In production, you might want a separate daily counter
            return usage.count if usage.count > 0 else 0
        
        return 0
    
    async def get_usage_stats(self, user: User) -> Dict:
        """Get usage statistics for a user"""
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        stmt = select(APIUsage).where(
            APIUsage.user_id == user.id,
            APIUsage.month == current_month
        )
        
        result = await self.db.execute(stmt)
        usage_records = result.scalars().all()
        
        stats = {}
        for usage in usage_records:
            limit = RateLimitConfig.get_monthly_limit(usage.api_type)
            stats[usage.api_type] = {
                "used": usage.count,
                "limit": limit,
                "remaining": limit - usage.count,
                "last_used": usage.last_used.isoformat() if usage.last_used else None
            }
        
        return stats


def get_usage_tracker(db: AsyncSession) -> UsageTracker:
    """Dependency to get usage tracker"""
    return UsageTracker(db)

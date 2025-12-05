"""
API Rate Limit Configuration

Centralized configuration for API rate limits. Easy to adjust without code changes.

Author: PawMatch Team
"""

from typing import Dict


class RateLimitConfig:
    """
    Configuration for API rate limits.
    
    Limits are defined per month per user for external API calls (Gemini, etc.)
    to control costs and prevent abuse.
    """
    
    # Monthly limits per user for external API calls
    MONTHLY_LIMITS: Dict[str, int] = {
        'research': 2,           # Reduced for cost safety
        'chat_gemini': 5,        # Limit unchanged
        'video_generation': 0,   # Disabled for cost safety
        'image_generation': 0,   # Disabled for cost safety
    }
    
    # Override for premium users (future feature)
    PREMIUM_MONTHLY_LIMITS: Dict[str, int] = {
        'research': 50,
        'chat_gemini': 100,
        'video_generation': 20,
        'image_generation': 50,
    }
    
    # Daily limits (additional safety net)
    DAILY_LIMITS: Dict[str, int] = {
        'research': 1,  # Consistent with monthly limit of 2
        'chat_gemini': 1,
        'video_generation': 0,
        'image_generation': 0,
    }
    
    @classmethod
    def get_monthly_limit(cls, api_type: str, is_premium: bool = False) -> int:
        """
        Get monthly limit for an API type.
        
        Args:
            api_type: Type of API ('research', 'chat_gemini', etc.)
            is_premium: Whether user has premium subscription
            
        Returns:
            Monthly limit for this API type
        """
        limits = cls.PREMIUM_MONTHLY_LIMITS if is_premium else cls.MONTHLY_LIMITS
        return limits.get(api_type, 5)  # Default to 5 if not specified
    
    @classmethod
    def get_daily_limit(cls, api_type: str) -> int:
        """
        Get daily limit for an API type.
        
        Args:
            api_type: Type of API
            
        Returns:
            Daily limit for this API type
        """
        return cls.DAILY_LIMITS.get(api_type, 3)  # Default to 3 if not specified
    
    @classmethod
    def get_all_limits(cls) -> Dict:
        """Get all configured limits"""
        return {
            'monthly': cls.MONTHLY_LIMITS,
            'daily': cls.DAILY_LIMITS,
            'premium_monthly': cls.PREMIUM_MONTHLY_LIMITS
        }

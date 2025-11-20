"""
Redis Cache Service

Provides caching functionality for sessions, match results, and breed data.

Author: PawMatch Team
Version: 1.0.0
"""

import json
from typing import Optional, Any, Dict, List
import redis
from app.core.config import get_settings


class CacheService:
    """
    Redis-based caching service.
    
    Provides methods for caching sessions, match results, and breed data
    with appropriate TTL (Time To Live) values.
    
    Attributes:
        redis_client (redis.Redis): Redis client instance
        
    Example:
        >>> cache = CacheService()
        >>> cache.set_session("session_123", {"profile": {...}}, ttl=3600)
        >>> session = cache.get_session("session_123")
    """
    
    def __init__(self):
        """Initialize Redis connection."""
        settings = get_settings()
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.redis = self.redis_client
        except Exception:
            # Redis is optional, use None if unavailable
            self.redis_client = None
            self.redis = None
    
    async def connect(self):
        """Test Redis connection (for async compatibility)."""
        if self.redis_client:
            try:
                self.redis_client.ping()
                return True
            except Exception:
                return False
        return False
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            self.redis_client.close()
        
    # Session Caching (TTL: 24 hours)
    
    def set_session(self, session_id: str, session_data: Dict[str, Any], ttl: int = 86400) -> bool:
        """
        Cache session data.
        
        Args:
            session_id (str): Unique session identifier
            session_data (dict): Session data to cache
            ttl (int): Time to live in seconds (default: 24 hours)
            
        Returns:
            bool: True if successful
        """
        try:
            key = f"session:{session_id}"
            self.redis_client.setex(key, ttl, json.dumps(session_data))
            return True
        except Exception as e:
            print(f"Cache error (set_session): {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached session data.
        
        Args:
            session_id (str): Unique session identifier
            
        Returns:
            Optional[dict]: Session data or None if not found
        """
        try:
            key = f"session:{session_id}"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Cache error (get_session): {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete cached session."""
        try:
            key = f"session:{session_id}"
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache error (delete_session): {e}")
            return False
    
    # Match Results Caching (TTL: 1 hour)
    
    def set_match_results(self, session_id: str, results: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Cache match results.
        
        Args:
            session_id (str): Unique session identifier
            results (dict): Match results to cache
            ttl (int): Time to live in seconds (default: 1 hour)
            
        Returns:
            bool: True if successful
        """
        try:
            key = f"match:{session_id}:results"
            self.redis_client.setex(key, ttl, json.dumps(results))
            return True
        except Exception as e:
            print(f"Cache error (set_match_results): {e}")
            return False
    
    def get_match_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached match results."""
        try:
            key = f"match:{session_id}:results"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Cache error (get_match_results): {e}")
            return None
    
    # Breed Data Caching (TTL: 7 days)
    
    def set_breed_data(self, breed_name: str, breed_data: Dict[str, Any], ttl: int = 604800) -> bool:
        """
        Cache breed data.
        
        Args:
            breed_name (str): Breed name
            breed_data (dict): Breed data to cache
            ttl (int): Time to live in seconds (default: 7 days)
            
        Returns:
            bool: True if successful
        """
        try:
            key = f"breed:{breed_name}:details"
            self.redis_client.setex(key, ttl, json.dumps(breed_data))
            return True
        except Exception as e:
            print(f"Cache error (set_breed_data): {e}")
            return False
    
    def get_breed_data(self, breed_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached breed data."""
        try:
            key = f"breed:{breed_name}:details"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Cache error (get_breed_data): {e}")
            return None
    
    # Breed List Caching
    
    def set_breed_list(self, breeds: List[str], ttl: int = 604800) -> bool:
        """Cache list of all breeds."""
        try:
            key = "breed:all:list"
            self.redis_client.setex(key, ttl, json.dumps(breeds))
            return True
        except Exception as e:
            print(f"Cache error (set_breed_list): {e}")
            return False
    
    def get_breed_list(self) -> Optional[List[str]]:
        """Retrieve cached breed list."""
        try:
            key = "breed:all:list"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Cache error (get_breed_list): {e}")
            return None
    
    # Popular Breeds Tracking
    
    def increment_breed_view(self, breed_name: str) -> bool:
        """Increment view count for a breed."""
        try:
            key = "breeds:popular:24h"
            self.redis_client.zincrby(key, 1, breed_name)
            self.redis_client.expire(key, 86400)  # 24 hours
            return True
        except Exception as e:
            print(f"Cache error (increment_breed_view): {e}")
            return False
    
    def get_popular_breeds(self, limit: int = 10) -> List[tuple]:
        """
        Get most popular breeds.
        
        Args:
            limit (int): Number of breeds to return
            
        Returns:
            List[tuple]: List of (breed_name, view_count) tuples
        """
        try:
            key = "breeds:popular:24h"
            return self.redis_client.zrevrange(key, 0, limit - 1, withscores=True)
        except Exception as e:
            print(f"Cache error (get_popular_breeds): {e}")
            return []
    
    # Rate Limiting
    
    def check_rate_limit(self, user_id: str, endpoint: str, max_requests: int = 100, window: int = 60) -> bool:
        """
        Check if user has exceeded rate limit.
        
        Args:
            user_id (str): User identifier
            endpoint (str): API endpoint
            max_requests (int): Maximum requests allowed
            window (int): Time window in seconds
            
        Returns:
            bool: True if within limit, False if exceeded
        """
        try:
            key = f"ratelimit:{user_id}:{endpoint}"
            current = self.redis_client.incr(key)
            
            if current == 1:
                self.redis_client.expire(key, window)
            
            return current <= max_requests
        except Exception as e:
            print(f"Cache error (check_rate_limit): {e}")
            return True  # Allow on error
    
    # Utility Methods
    
    def clear_all(self) -> bool:
        """Clear all cached data (use with caution)."""
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            print(f"Cache error (clear_all): {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            info = self.redis_client.info()
            return {
                "connected": True,
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "total_keys": self.redis_client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            print(f"Cache error (get_stats): {e}")
            return {"connected": False, "error": str(e)}

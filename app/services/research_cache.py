"""
Research Results Caching Service

Caches breed research results to avoid repeated API calls.
Uses in-memory caching with TTL (Time To Live).

Author: PawMatch Team
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class ResearchCache:
    """In-memory cache for research results"""
    
    def __init__(self, ttl_hours: int = 24):
        """
        Initialize research cache.
        
        Args:
            ttl_hours: Time to live in hours (default 24 hours)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(hours=ttl_hours)
    
    def _generate_key(self, breed_name: str, query: Optional[str] = None, **kwargs) -> str:
        """
        Generate cache key from parameters.
        
        Args:
            breed_name: Breed name
            query: User query
            **kwargs: Additional parameters
            
        Returns:
            Cache key hash
        """
        # Normalize breed name
        breed_normalized = breed_name.lower().strip()
        
        # Create a unique key from all parameters
        key_data = {
            'breed': breed_normalized,
            'query': query.lower().strip() if query else None,
            **kwargs
        }
        
        # Generate hash
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, breed_name: str, query: Optional[str] = None, **kwargs) -> Optional[Dict]:
        """
        Get cached research result.
        
        Args:
            breed_name: Breed name
            query: User query
            **kwargs: Additional parameters
            
        Returns:
            Cached result or None if not found/expired
        """
        key = self._generate_key(breed_name, query, **kwargs)
        
        if key not in self.cache:
            return None
        
        cached_data = self.cache[key]
        
        # Check if expired
        if datetime.utcnow() > cached_data['expires_at']:
            # Remove expired entry
            del self.cache[key]
            logger.info(f"Cache expired for breed: {breed_name}")
            return None
        
        logger.info(f"Cache hit for breed: {breed_name}")
        return cached_data['result']
    
    def set(self, result: Dict, breed_name: str, query: Optional[str] = None, **kwargs):
        """
        Store research result in cache.
        
        Args:
            result: Research result to cache
            breed_name: Breed name
            query: User query
            **kwargs: Additional parameters
        """
        key = self._generate_key(breed_name, query, **kwargs)
        
        self.cache[key] = {
            'result': result,
            'cached_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + self.ttl,
            'breed': breed_name
        }
        
        logger.info(f"Cached research for breed: {breed_name}, expires in {self.ttl}")
    
    def clear(self):
        """Clear all cached results"""
        self.cache.clear()
        logger.info("Research cache cleared")
    
    def cleanup_expired(self):
        """Remove expired entries from cache"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, data in self.cache.items()
            if now > data['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        now = datetime.utcnow()
        valid_entries = sum(1 for data in self.cache.values() if now <= data['expires_at'])
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.cache) - valid_entries,
            'ttl_hours': self.ttl.total_seconds() / 3600
        }


# Singleton instance
_research_cache = None

def get_research_cache() -> ResearchCache:
    """Get singleton research cache instance"""
    global _research_cache
    if _research_cache is None:
        _research_cache = ResearchCache(ttl_hours=24)
    return _research_cache

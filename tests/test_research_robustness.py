"""
Research API Robustness Tests

Tests for rate limiting, caching, authentication, and error handling.

Author: PawMatch Team
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi import HTTPException
from app.services.research_cache import ResearchCache
from app.services.usage_tracker import UsageTracker
from app.config.rate_limits import RateLimitConfig
from app.db.models.user import User
from app.db.models.api_usage import APIUsage


class TestResearchCache:
    """Test research caching functionality"""
    
    def test_cache_miss(self):
        """Test cache miss returns None"""
        cache = ResearchCache(ttl_hours=24)
        result = cache.get("Golden Retriever")
        assert result is None
    
    def test_cache_hit(self):
        """Test successful cache retrieval"""
        cache = ResearchCache(ttl_hours=24)
        
        test_data = {"breed_research": "Test data", "success": True}
        cache.set(test_data, "Golden Retriever")
        
        result = cache.get("Golden Retriever")
        assert result is not None
        assert result == test_data
    
    def test_cache_key_normalization(self):
        """Test that breed names are normalized (case-insensitive)"""
        cache = ResearchCache(ttl_hours=24)
        
        test_data = {"breed_research": "Test data"}
        cache.set(test_data, "Golden Retriever")
        
        # Different casing should still hit cache
        result = cache.get("golden retriever")
        assert result is not None
    
    def test_cache_with_query(self):
        """Test cache differentiation with queries"""
        cache = ResearchCache(ttl_hours=24)
        
        data1 = {"answer": "Yes, they're great"}
        data2 = {"answer": "They need exercise"}
        
        cache.set(data1, "Golden Retriever", query="good with kids?")
        cache.set(data2, "Golden Retriever", query="exercise needs?")
        
        result1 = cache.get("Golden Retriever", query="good with kids?")
        result2 = cache.get("Golden Retriever", query="exercise needs?")
        
        assert result1 != result2
        assert result1 == data1
        assert result2 == data2
    
    def test_cache_expiration(self):
        """Test that cache expires after TTL"""
        cache = ResearchCache(ttl_hours=0)  # Expires immediately
        
        test_data = {"breed_research": "Test data"}
        cache.set(test_data, "Golden Retriever")
        
        # Should be expired
        result = cache.get("Golden Retriever")
        assert result is None
    
    def test_cache_clear(self):
        """Test clearing entire cache"""
        cache = ResearchCache(ttl_hours=24)
        
        cache.set({"data": 1}, "Breed1")
        cache.set({"data": 2}, "Breed2")
        
        assert cache.get("Breed1") is not None
        assert cache.get("Breed2") is not None
        
        cache.clear()
        
        assert cache.get("Breed1") is None
        assert cache.get("Breed2") is None
    
    def test_cache_stats(self):
        """Test cache statistics"""
        cache = ResearchCache(ttl_hours=24)
        
        cache.set({"data": 1}, "Breed1")
        cache.set({"data": 2}, "Breed2")
        
        stats = cache.get_stats()
        
        assert stats['total_entries'] == 2
        assert stats['valid_entries'] == 2
        assert stats['ttl_hours'] == 24


class TestRateLimitConfig:
    """Test rate limit configuration"""
    
    def test_default_limits(self):
        """Test default monthly limits"""
        assert RateLimitConfig.MONTHLY_LIMITS['research'] == 2
        assert RateLimitConfig.MONTHLY_LIMITS['chat_gemini'] == 5
    
    def test_get_monthly_limit(self):
        """Test getting monthly limit for API type"""
        limit = RateLimitConfig.get_monthly_limit('research')
        assert limit == 2
        
        # Test unknown API type gets default
        limit = RateLimitConfig.get_monthly_limit('unknown_api')
        assert limit == 5
    
    def test_premium_limits(self):
        """Test premium user limits"""
        regular_limit = RateLimitConfig.get_monthly_limit('research', is_premium=False)
        premium_limit = RateLimitConfig.get_monthly_limit('research', is_premium=True)
        
        assert premium_limit > regular_limit
        assert premium_limit == 50
    
    def test_daily_limits(self):
        """Test daily limits"""
        daily = RateLimitConfig.get_daily_limit('research')
        assert daily == 1


@pytest.mark.asyncio
class TestUsageTracker:
    """Test API usage tracking"""
    
    async def test_first_usage(self, async_session):
        """Test first API usage creates record"""
        tracker = UsageTracker(async_session)
        user = User(id=1, email="test@example.com")
        
        # Mock check_and_increment
        with patch.object(tracker, '_get_or_create_usage') as mock_get:
            usage = APIUsage(
                user_id=1,
                api_type='research',
                endpoint='/research/breed',
                month=datetime.utcnow().strftime("%Y-%m"),
                count=0
            )
            mock_get.return_value = usage
            
            result = await tracker.check_and_increment(
                user=user,
                api_type='research',
                endpoint='/research/breed'
            )
            
            assert result['allowed'] == True
            assert result['monthly_usage'] == 1
    
    async def test_usage_limit_exceeded(self, async_session):
        """Test rate limit enforcement"""
        tracker = UsageTracker(async_session)
        user = User(id=1, email="test@example.com")
        
        # Mock usage at limit
        with patch.object(tracker, '_get_or_create_usage') as mock_get:
            usage = APIUsage(
                user_id=1,
                api_type='research',
                endpoint='/research/breed',
                month=datetime.utcnow().strftime("%Y-%m"),
                count=5  # At limit
            )
            mock_get.return_value = usage
            
            with pytest.raises(HTTPException) as exc_info:
                await tracker.check_and_increment(
                    user=user,
                    api_type='research',
                    endpoint='/research/breed'
                )
            
            assert exc_info.value.status_code == 429
            assert "Monthly limit exceeded" in str(exc_info.value.detail)


class TestErrorHandling:
    """Test improved error handling"""
    
    def test_specific_exception_types(self):
        """Test that we're catching specific exceptions, not bare except"""
        # This is a code quality test
        import app.services.search_service as search_module
        import inspect
        
        source = inspect.getsource(search_module.SearchService._extract_sources)
        
        # Should not have bare except
        assert "except:" not in source or "except (" in source
        
        # Should have specific exception types
        assert "AttributeError" in source or "TypeError" in source


class TestInputValidation:
    """Test input validation"""
    
    def test_breed_name_validation(self):
        """Test breed name is validated"""
        from app.routes.research import BreedResearchRequest
        from pydantic import ValidationError
        
        # Empty breed name should fail
        with pytest.raises(ValidationError):
            BreedResearchRequest(breed_name="")
        
        # Too long breed name should fail
        with pytest.raises(ValidationError):
            BreedResearchRequest(breed_name="x" * 101)
        
        # Valid breed name should pass
        request = BreedResearchRequest(breed_name="Golden Retriever")
        assert request.breed_name == "Golden Retriever"
    
    def test_query_validation(self):
        """Test user query is validated"""
        from app.routes.research import BreedResearchRequest
        from pydantic import ValidationError
        
        # Too long query should fail
        with pytest.raises(ValidationError):
            BreedResearchRequest(
                breed_name="Golden Retriever",
                user_query="x" * 501
            )
        
        # Valid query should pass
        request = BreedResearchRequest(
            breed_name="Golden Retriever",
            user_query="Are they good with kids?"
        )
        assert request.user_query == "Are they good with kids?"


class TestAuthentication:
    """Test authentication requirements"""
    
    def test_research_endpoint_requires_auth(self):
        """Test that research endpoints require authentication"""
        from app.routes.research import research_breed
        import inspect
        
        # Check function signature includes current_user dependency
        sig = inspect.signature(research_breed)
        params = sig.parameters
        
        assert 'current_user' in params
        assert 'db' in params


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

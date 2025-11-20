"""
Comprehensive Backend Test Suite

Tests all major backend functionality including database, cache, APIs, and services.

Usage:
    pytest tests/test_comprehensive.py -v
    
Or run directly:
    python tests/test_comprehensive.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.db.models import Breed, BreedImage, Session, ChatMessage
from app.services.breed_service import BreedService
from app.services.cache_service import CacheService
from app.models.user_profile import UserProfile


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def pass_test(self, name: str):
        self.passed += 1
        print(f"  ✅ {name}")
    
    def fail_test(self, name: str, error: str):
        self.failed += 1
        self.errors.append((name, error))
        print(f"  ❌ {name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*70}")
        print(f"RESULTS: {self.passed}/{total} tests passed")
        if self.failed > 0:
            print(f"\nFailed tests:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        print(f"{'='*70}")
        return self.failed == 0


async def test_database():
    """Test database connectivity and data."""
    print("\n1️⃣  DATABASE TESTS")
    print("-" * 70)
    results = TestResults()
    
    try:
        async with AsyncSessionLocal() as db:
            # Test 1: Database connection
            try:
                await db.execute(select(1))
                results.pass_test("Database connection")
            except Exception as e:
                results.fail_test("Database connection", str(e))
            
            # Test 2: Breeds table
            try:
                count = await db.scalar(select(func.count()).select_from(Breed))
                if count > 0:
                    results.pass_test(f"Breeds table ({count} breeds)")
                else:
                    results.fail_test("Breeds table", "No breeds found")
            except Exception as e:
                results.fail_test("Breeds table", str(e))
            
            # Test 3: Images table
            try:
                count = await db.scalar(select(func.count()).select_from(BreedImage))
                if count > 0:
                    results.pass_test(f"Images table ({count} images)")
                else:
                    results.fail_test("Images table", "No images found")
            except Exception as e:
                results.fail_test("Images table", str(e))
            
            # Test 4: Sample breed query
            try:
                result = await db.execute(select(Breed).limit(1))
                breed = result.scalar_one_or_none()
                if breed and breed.traits:
                    results.pass_test(f"Breed data structure (sample: {breed.name})")
                else:
                    results.fail_test("Breed data structure", "Invalid breed data")
            except Exception as e:
                results.fail_test("Breed data structure", str(e))
            
            # Test 5: Breed-Image relationship
            try:
                result = await db.execute(
                    select(Breed).limit(1)
                )
                breed = result.scalar_one()
                img_count = await db.scalar(
                    select(func.count()).select_from(BreedImage).where(BreedImage.breed_id == breed.id)
                )
                if img_count > 0:
                    results.pass_test(f"Breed-Image relationship ({img_count} images for {breed.name})")
                else:
                    results.fail_test("Breed-Image relationship", "No images found for breed")
            except Exception as e:
                results.fail_test("Breed-Image relationship", str(e))
    
    except Exception as e:
        results.fail_test("Database tests", str(e))
    
    return results.summary()


async def test_breed_service():
    """Test BreedService."""
    print("\n2️⃣  BREED SERVICE TESTS")
    print("-" * 70)
    results = TestResults()
    
    service = BreedService()
    
    # Test 1: Get all breeds
    try:
        breeds = await service.get_all_breeds()
        if len(breeds) > 0:
            results.pass_test(f"Get all breeds ({len(breeds)} breeds)")
        else:
            results.fail_test("Get all breeds", "No breeds returned")
    except Exception as e:
        results.fail_test("Get all breeds", str(e))
        breeds = []
    
    # Test 2: Get breed traits
    if breeds:
        try:
            traits = await service.get_breed_traits(breeds[0])
            if traits and hasattr(traits, 'energy_level'):
                results.pass_test(f"Get breed traits ({breeds[0]})")
            else:
                results.fail_test("Get breed traits", "Invalid traits structure")
        except Exception as e:
            results.fail_test("Get breed traits", str(e))
    
    # Test 3: Get breed details
    if breeds:
        try:
            details = await service.get_breed_details(breeds[0])
            if details and details.images:
                results.pass_test(f"Get breed details ({len(details.images)} images)")
            else:
                results.fail_test("Get breed details", "No images in details")
        except Exception as e:
            results.fail_test("Get breed details", str(e))
    
    # Test 4: Get breed images
    if breeds:
        try:
            images = await service.get_breed_images(breeds[0], count=5)
            if len(images) > 0:
                results.pass_test(f"Get breed images ({len(images)} images)")
            else:
                results.fail_test("Get breed images", "No images returned")
        except Exception as e:
            results.fail_test("Get breed images", str(e))
    
    # Test 5: Search breeds
    try:
        results_list = await service.search_breeds("Lab", limit=5)
        if len(results_list) > 0:
            results.pass_test(f"Search breeds ({len(results_list)} results for 'Lab')")
        else:
            results.fail_test("Search breeds", "No search results")
    except Exception as e:
        results.fail_test("Search breeds", str(e))
    
    # Test 6: Get breed count
    try:
        count = await service.get_breed_count()
        if count > 0:
            results.pass_test(f"Get breed count ({count})")
        else:
            results.fail_test("Get breed count", "Count is 0")
    except Exception as e:
        results.fail_test("Get breed count", str(e))
    
    return results.summary()


def test_cache_service():
    """Test CacheService."""
    print("\n3️⃣  CACHE SERVICE TESTS")
    print("-" * 70)
    results = TestResults()
    
    try:
        cache = CacheService()
        
        # Test 1: Connection
        try:
            stats = cache.get_stats()
            if stats.get("connected"):
                results.pass_test(f"Redis connection (v{stats.get('version')})")
            else:
                results.fail_test("Redis connection", "Not connected")
        except Exception as e:
            results.fail_test("Redis connection", str(e))
            return results.summary()
        
        # Test 2: Session caching
        try:
            test_data = {"profile": {"living_space": "house"}}
            cache.set_session("test_123", test_data, ttl=10)
            retrieved = cache.get_session("test_123")
            if retrieved == test_data:
                results.pass_test("Session caching")
            else:
                results.fail_test("Session caching", "Data mismatch")
            cache.delete_session("test_123")
        except Exception as e:
            results.fail_test("Session caching", str(e))
        
        # Test 3: Match results caching
        try:
            test_results = {"top_three": [{"breed": "Lab", "score": 95}]}
            cache.set_match_results("test_123", test_results, ttl=10)
            retrieved = cache.get_match_results("test_123")
            if retrieved == test_results:
                results.pass_test("Match results caching")
            else:
                results.fail_test("Match results caching", "Data mismatch")
        except Exception as e:
            results.fail_test("Match results caching", str(e))
        
        # Test 4: Breed data caching
        try:
            test_breed = {"name": "Labrador", "traits": {}}
            cache.set_breed_data("Labrador", test_breed, ttl=10)
            retrieved = cache.get_breed_data("Labrador")
            if retrieved == test_breed:
                results.pass_test("Breed data caching")
            else:
                results.fail_test("Breed data caching", "Data mismatch")
        except Exception as e:
            results.fail_test("Breed data caching", str(e))
        
        # Test 5: Rate limiting
        try:
            allowed = cache.check_rate_limit("user_test", "/api/test", max_requests=5, window=60)
            if allowed:
                results.pass_test("Rate limiting")
            else:
                results.fail_test("Rate limiting", "Blocked unexpectedly")
        except Exception as e:
            results.fail_test("Rate limiting", str(e))
    
    except Exception as e:
        results.fail_test("Cache service initialization", str(e))
    
    return results.summary()


async def run_all_tests():
    """Run all test suites."""
    print("\n" + "="*70)
    print("COMPREHENSIVE BACKEND TEST SUITE")
    print("="*70)
    
    all_passed = True
    
    # Database tests
    all_passed &= await test_database()
    
    # Breed service tests
    all_passed &= await test_breed_service()
    
    # Cache service tests
    all_passed &= test_cache_service()
    
    # Final summary
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*70)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

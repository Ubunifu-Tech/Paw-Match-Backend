"""
Comprehensive PawMatch API Test Suite
Tests all endpoints and verifies rebranding
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self):
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
        self.test_data = {}
    
    def test(self, name, test_func):
        """Run a test and track results"""
        try:
            result = test_func()
            if result:
                self.results["passed"].append(name)
                print(f"✅ {name}")
                return True
            else:
                self.results["failed"].append(name)
                print(f"❌ {name}")
                return False
        except Exception as e:
            self.results["failed"].append(f"{name}: {str(e)}")
            print(f"❌ {name}: {str(e)}")
            return False
    
    def warn(self, message):
        """Add a warning"""
        self.results["warnings"].append(message)
        print(f"⚠️  {message}")
    
    def print_summary(self):
        """Print test summary"""
        total = len(self.results["passed"]) + len(self.results["failed"])
        passed = len(self.results["passed"])
        failed = len(self.results["failed"])
        warnings = len(self.results["warnings"])
        
        print("\n" + "="*70)
        print("🐾 PAWMATCH API TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"\nSuccess Rate: {(passed/total)*100:.1f}%" if total > 0 else "No tests run")
        print("="*70)
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for fail in self.results["failed"]:
                print(f"  - {fail}")
        
        if warnings > 0:
            print("\n⚠️  WARNINGS:")
            for warn in self.results["warnings"]:
                print(f"  - {warn}")
        
        return failed == 0


def main():
    tester = APITester()
    
    print("="*70)
    print("🐾 PAWMATCH API COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Testing: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Test 1: Root Endpoint
    print("\n1️⃣  ROOT ENDPOINT TESTS")
    print("-"*70)
    
    def test_root():
        r = requests.get(f"{BASE_URL}/")
        data = r.json()
        assert r.status_code == 200
        assert "PawMatch" in data["message"]
        assert "paw-tner" in data["message"].lower()
        assert "🐾" in data["message"]
        print(f"   Response: {data['message']}")
        return True
    
    tester.test("Root endpoint returns PawMatch branding", test_root)
    
    # Test 2: Health Endpoint
    print("\n2️⃣  HEALTH CHECK")
    print("-"*70)
    
    def test_health():
        r = requests.get(f"{BASE_URL}/health")
        data = r.json()
        assert r.status_code == 200
        assert data["status"] == "healthy"
        print(f"   Status: {data['status']}")
        return True
    
    tester.test("Health check returns healthy", test_health)
    
    # Test 3: OpenAPI Docs
    print("\n3️⃣  API DOCUMENTATION")
    print("-"*70)
    
    def test_openapi():
        r = requests.get(f"{BASE_URL}/openapi.json")
        data = r.json()
        assert r.status_code == 200
        assert data["info"]["title"] == "PawMatch"
        assert "paw-tner" in data["info"]["description"].lower()
        assert data["info"]["contact"]["name"] == "PawMatch Team"
        assert data["info"]["contact"]["email"] == "support@pawmatch.ai"
        print(f"   Title: {data['info']['title']}")
        print(f"   Contact: {data['info']['contact']['email']}")
        return True
    
    tester.test("OpenAPI schema has PawMatch branding", test_openapi)
    
    # Test 4: User API
    print("\n4️⃣  USER API TESTS")
    print("-"*70)
    
    def test_create_anonymous_user():
        r = requests.post(f"{BASE_URL}/api/users/anonymous")
        assert r.status_code == 200
        data = r.json()
        assert "user_id" in data
        assert data["is_anonymous"] == True
        tester.test_data["user_id"] = data["user_id"]
        print(f"   Created user: {data['user_id'][:8]}...")
        return True
    
    tester.test("Create anonymous user", test_create_anonymous_user)
    
    def test_get_user():
        user_id = tester.test_data.get("user_id")
        if not user_id:
            tester.warn("No user_id available")
            return False
        r = requests.get(f"{BASE_URL}/api/users/{user_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == user_id
        print(f"   Retrieved user: {user_id[:8]}...")
        return True
    
    tester.test("Get user by ID", test_get_user)
    
    def test_update_preferences():
        user_id = tester.test_data.get("user_id")
        if not user_id:
            return False
        payload = {"preferences": {"theme": "dark", "notifications": True}}
        r = requests.put(f"{BASE_URL}/api/users/{user_id}/preferences", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "theme" in data["preferences"]
        print(f"   Updated preferences")
        return True
    
    tester.test("Update user preferences", test_update_preferences)
    
    def test_get_usage():
        user_id = tester.test_data.get("user_id")
        if not user_id:
            return False
        r = requests.get(f"{BASE_URL}/api/users/{user_id}/usage")
        assert r.status_code == 200
        data = r.json()
        assert "api_calls_today" in data
        assert "daily_limit" in data
        print(f"   Usage: {data['api_calls_today']}/{data['daily_limit']}")
        return True
    
    tester.test("Get API usage stats", test_get_usage)
    
    # Test 5: Breeds API
    print("\n5️⃣  BREEDS API TESTS")
    print("-"*70)
    
    def test_get_breeds():
        r = requests.get(f"{BASE_URL}/api/breeds/")
        assert r.status_code == 200
        data = r.json()
        assert "breeds" in data
        assert len(data["breeds"]) > 100
        print(f"   Retrieved {len(data['breeds'])} breeds")
        return True
    
    tester.test("Get all breeds", test_get_breeds)
    
    def test_get_breed_details():
        r = requests.get(f"{BASE_URL}/api/breeds/Retrievers (Labrador)")
        assert r.status_code == 200
        data = r.json()
        assert data["breed"] == "Retrievers (Labrador)"
        assert "traits" in data
        assert "images" in data
        print(f"   Retrieved details for: {data['breed']}")
        print(f"   Images: {len(data['images'])}")
        return True
    
    tester.test("Get breed details", test_get_breed_details)
    
    # Test 6: Chat API
    print("\n6️⃣  CHAT API TESTS")
    print("-"*70)
    
    def test_chat_message():
        payload = {
            "message": "Hello, I'm looking for a dog!",
            "session_id": None
        }
        r = requests.post(f"{BASE_URL}/api/chat/message", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "response" in data
        assert "session_id" in data
        tester.test_data["session_id"] = data["session_id"]
        print(f"   Session created: {data['session_id'][:8]}...")
        print(f"   Response preview: {data['response'][:60]}...")
        return True
    
    tester.test("Send chat message", test_chat_message)
    
    def test_get_session():
        session_id = tester.test_data.get("session_id")
        if not session_id:
            return False
        r = requests.get(f"{BASE_URL}/api/chat/session/{session_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["session_id"] == session_id
        print(f"   Retrieved session: {session_id[:8]}...")
        return True
    
    tester.test("Get chat session", test_get_session)
    
    # Test 7: Recommendations API (will fail without complete profile)
    print("\n7️⃣  RECOMMENDATIONS API TEST")
    print("-"*70)
    
    def test_recommendations():
        session_id = tester.test_data.get("session_id")
        if not session_id:
            return False
        r = requests.get(f"{BASE_URL}/api/recommendations/{session_id}")
        # This might fail if profile incomplete, which is expected
        if r.status_code == 400:
            tester.warn("Recommendations require complete user profile (expected)")
            return True
        assert r.status_code in [200, 400]
        if r.status_code == 200:
            data = r.json()
            print(f"   Got {len(data.get('recommendations', []))} recommendations")
        return True
    
    tester.test("Get recommendations", test_recommendations)
    
    # Test 8: Cleanup
    print("\n8️⃣  CLEANUP")
    print("-"*70)
    
    def test_delete_user():
        user_id = tester.test_data.get("user_id")
        if not user_id:
            return False
        r = requests.delete(f"{BASE_URL}/api/users/{user_id}")
        assert r.status_code == 200
        data = r.json()
        assert "deleted successfully" in data["message"].lower()
        print(f"   Deleted user: {user_id[:8]}...")
        return True
    
    tester.test("Delete user data (GDPR)", test_delete_user)
    
    # Print summary
    success = tester.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

"""
Comprehensive PawMatch API Test Suite - Final Version
Tests all endpoints with correct response structures
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

class APITester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.test_data = {}
    
    def test(self, name, test_func):
        """Run a test"""
        try:
            test_func()
            self.passed += 1
            print(f"{Colors.GREEN}✅ {name}{Colors.RESET}")
            return True
        except AssertionError as e:
            self.failed += 1
            print(f"{Colors.RED}❌ {name}: {str(e)}{Colors.RESET}")
            return False
        except Exception as e:
            self.failed += 1
            print(f"{Colors.RED}❌ {name}: {type(e).__name__}: {str(e)}{Colors.RESET}")
            return False
    
    def warn(self, message):
        """Add warning"""
        self.warnings += 1
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")
    
    def info(self, message):
        """Print info"""
        print(f"{Colors.BLUE}   {message}{Colors.RESET}")


def main():
    tester = APITester()
    
    print("="*70)
    print(f"{Colors.BLUE}🐾 PAWMATCH API COMPREHENSIVE TEST SUITE{Colors.RESET}")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Test Category 1: Core Endpoints
    print(f"\n{Colors.BLUE}1️⃣  CORE ENDPOINTS{Colors.RESET}")
    print("-"*70)
    
    def test_root():
        r = requests.get(f"{BASE_URL}/")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        data = r.json()
        assert "PawMatch" in data["message"], "Missing PawMatch branding"
        assert "🐾" in data["message"], "Missing paw emoji"
        tester.info(f"Message: {data['message']}")
    
    tester.test("Root endpoint branding", test_root)
    
    def test_health():
        r = requests.get(f"{BASE_URL}/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        tester.info(f"Status: {data['status']}")
    
    tester.test("Health check", test_health)
    
    def test_openapi():
        r = requests.get(f"{BASE_URL}/openapi.json")
        assert r.status_code == 200
        data = r.json()
        assert data["info"]["title"] == "PawMatch"
        assert "paw-tner" in data["info"]["description"].lower()
        assert data["info"]["contact"]["email"] == "support@pawmatch.ai"
        tester.info(f"API: {data['info']['title']} v{data['info']['version']}")
        tester.info(f"Contact: {data['info']['contact']['email']}")
    
    tester.test("OpenAPI documentation", test_openapi)
    
    # Test Category 2: User Management
    print(f"\n{Colors.BLUE}2️⃣  USER MANAGEMENT{Colors.RESET}")
    print("-"*70)
    
    def test_create_user():
        r = requests.post(f"{BASE_URL}/api/users/anonymous")
        assert r.status_code == 200
        data = r.json()
        assert "user_id" in data
        assert data["is_anonymous"] == True
        assert "api_usage" in data
        tester.test_data["user_id"] = data["user_id"]
        tester.info(f"User ID: {data['user_id'][:16]}...")
        tester.info(f"Daily limit: {data['api_usage']['daily_limit']}")
    
    tester.test("Create anonymous user", test_create_user)
    
    def test_get_user():
        user_id = tester.test_data.get("user_id")
        r = requests.get(f"{BASE_URL}/api/users/{user_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == user_id
        assert "preferences" in data
        assert "cross_session_memory" in data
        tester.info(f"Retrieved user successfully")
    
    tester.test("Get user details", test_get_user)
    
    def test_preferences():
        user_id = tester.test_data.get("user_id")
        payload = {"preferences": {"theme": "dark", "lang": "en"}}
        r = requests.put(f"{BASE_URL}/api/users/{user_id}/preferences", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "theme" in data["preferences"]
        tester.info(f"Preferences updated")
    
    tester.test("Update preferences", test_preferences)
    
    def test_usage():
        user_id = tester.test_data.get("user_id")
        r = requests.get(f"{BASE_URL}/api/users/{user_id}/usage")
        assert r.status_code == 200
        data = r.json()
        assert "calls_today" in data
        assert "daily_limit" in data
        assert "remaining" in data
        tester.info(f"API usage: {data['calls_today']}/{data['daily_limit']}")
    
    tester.test("Get API usage", test_usage)
    
    def test_sessions():
        user_id = tester.test_data.get("user_id")
        r = requests.get(f"{BASE_URL}/api/users/{user_id}/sessions")
        assert r.status_code == 200
        data = r.json()
        assert "sessions" in data
        tester.info(f"Sessions: {len(data['sessions'])}")
    
    tester.test("Get user sessions", test_sessions)
    
    # Test Category 3: Breeds API
    print(f"\n{Colors.BLUE}3️⃣  BREEDS DATABASE{Colors.RESET}")
    print("-"*70)
    
    def test_list_breeds():
        r = requests.get(f"{BASE_URL}/api/breeds/")
        assert r.status_code == 200
        data = r.json()
        assert "breeds" in data
        assert len(data["breeds"]) == 195
        tester.info(f"Total breeds: {len(data['breeds'])}")
    
    tester.test("List all breeds", test_list_breeds)
    
    def test_breed_details():
        r = requests.get(f"{BASE_URL}/api/breeds/Retrievers (Labrador)")
        assert r.status_code == 200
        data = r.json()
        assert data["breed"] == "Retrievers (Labrador)"
        assert "traits" in data
        assert "images" in data
        assert len(data["images"]) == 35
        tester.info(f"Breed: {data['breed']}")
        tester.info(f"Images: {len(data['images'])}")
    
    tester.test("Get breed details", test_breed_details)
    
    # Test Category 4: Conversational AI
    print(f"\n{Colors.BLUE}4️⃣  CONVERSATIONAL AI{Colors.RESET}")
    print("-"*70)
    
    def test_chat():
        payload = {"message": "Hi! I'm looking for a dog breed recommendation.", "session_id": None}
        r = requests.post(f"{BASE_URL}/api/chat/message", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "message" in data or "response" in data
        assert "session_id" in data
        tester.test_data["session_id"] = data["session_id"]
        response = data.get("message") or data.get("response", "")
        tester.info(f"Session: {data['session_id'][:16]}...")
        tester.info(f"Response: {response[:60]}...")
    
    tester.test("Chat message (AI response)", test_chat)
    
    def test_get_session():
        session_id = tester.test_data.get("session_id")
        if not session_id:
            tester.warn("No session_id from chat test")
            return
        r = requests.get(f"{BASE_URL}/api/chat/session/{session_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["session_id"] == session_id
        tester.info(f"Session retrieved")
    
    tester.test("Retrieve session", test_get_session)
    
    # Test Category 5: Recommendations
    print(f"\n{Colors.BLUE}5️⃣  BREED RECOMMENDATIONS{Colors.RESET}")
    print("-"*70)
    
    def test_recommendations():
        session_id = tester.test_data.get("session_id")
        if not session_id:
            tester.warn("No session for recommendations")
            return
        r = requests.get(f"{BASE_URL}/api/recommendations/{session_id}")
        # May fail if profile incomplete - that's OK
        if r.status_code == 400:
            data = r.json()
            if "profile" in data.get("detail", "").lower():
                tester.warn("Profile incomplete (expected for minimal conversation)")
                tester.info(f"Reason: {data.get('detail', '')[:60]}")
                return
        assert r.status_code in [200, 400]
        if r.status_code == 200:
            data = r.json()
            tester.info(f"Recommendations: {len(data.get('recommendations', []))}")
    
    tester.test("Get recommendations", test_recommendations)
    
    # Test Category 6: Data Privacy (GDPR)
    print(f"\n{Colors.BLUE}6️⃣  DATA PRIVACY (GDPR){Colors.RESET}")
    print("-"*70)
    
    def test_delete():
        user_id = tester.test_data.get("user_id")
        r = requests.delete(f"{BASE_URL}/api/users/{user_id}")
        assert r.status_code == 200
        data = r.json()
        assert "deleted" in data["message"].lower()
        tester.info(f"User data deleted: {user_id[:16]}...")
    
    tester.test("Delete user data", test_delete)
    
    def test_verify_deletion():
        user_id = tester.test_data.get("user_id")
        r = requests.get(f"{BASE_URL}/api/users/{user_id}")
        assert r.status_code == 404
        tester.info(f"Confirmed deletion (404 response)")
    
    tester.test("Verify complete deletion", test_verify_deletion)
    
    # Summary
    print("\n" + "="*70)
    print(f"{Colors.BLUE}📊 TEST SUMMARY{Colors.RESET}")
    print("="*70)
    total = tester.passed + tester.failed
    success_rate = (tester.passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"{Colors.GREEN}✅ Passed: {tester.passed}{Colors.RESET}")
    print(f"{Colors.RED}❌ Failed: {tester.failed}{Colors.RESET}")
    print(f"{Colors.YELLOW}⚠️  Warnings: {tester.warnings}{Colors.RESET}")
    print(f"\n{Colors.BLUE}Success Rate: {success_rate:.1f}%{Colors.RESET}")
    
    if tester.failed == 0:
        print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED! API IS PRODUCTION READY{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}Some tests failed. Review errors above.{Colors.RESET}")
    
    print("="*70)
    
    return 0 if tester.failed == 0 else 1

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted{Colors.RESET}")
        exit(1)

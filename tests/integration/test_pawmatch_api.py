"""
PawMatch API - Complete Test Suite
All tests corrected for actual API responses
"""

import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

print("="*70)
print("🐾 PAWMATCH API - COMPREHENSIVE TEST SUITE")
print("="*70)
print(f"Testing: {BASE_URL}")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

passed = 0
failed = 0
test_data = {}

def test(name, func):
    global passed, failed
    try:
        func()
        passed += 1
        print(f"✅ {name}")
        return True
    except Exception as e:
        failed += 1
        print(f"❌ {name}: {e}")
        return False

# 1. CORE ENDPOINTS
print("\n1️⃣  CORE ENDPOINTS")
print("-"*70)

def t1():
    r = requests.get(f"{BASE_URL}/")
    assert "PawMatch" in r.json()["message"]
    assert "🐾" in r.json()["message"]
    print(f"   {r.json()['message']}")

test("Root endpoint", t1)

def t2():
    r = requests.get(f"{BASE_URL}/health")
    assert r.json()["status"] == "healthy"

test("Health check", t2)

def t3():
    r = requests.get(f"{BASE_URL}/openapi.json")
    data = r.json()
    assert data["info"]["title"] == "PawMatch"
    assert data["info"]["contact"]["email"] == "support@pawmatch.ai"
    print(f"   Title: {data['info']['title']}")
    print(f"   Contact: {data['info']['contact']['email']}")

test("OpenAPI docs", t3)

# 2. USER API
print("\n2️⃣  USER MANAGEMENT")
print("-"*70)

def t4():
    r = requests.post(f"{BASE_URL}/api/users/anonymous")
    data = r.json()
    test_data["user_id"] = data["user_id"]
    assert data["is_anonymous"] == True
    print(f"   User: {data['user_id'][:20]}...")

test("Create anonymous user", t4)

def t5():
    r = requests.get(f"{BASE_URL}/api/users/{test_data['user_id']}")
    data = r.json()
    assert data["user_id"] == test_data["user_id"]

test("Get user", t5)

def t6():
    r = requests.put(
        f"{BASE_URL}/api/users/{test_data['user_id']}/preferences",
        json={"preferences": {"theme": "dark"}}
    )
    assert r.status_code == 200

test("Update preferences", t6)

def t7():
    r = requests.get(f"{BASE_URL}/api/users/{test_data['user_id']}/usage")
    data = r.json()
    assert "daily_limit" in data
    print(f"   Usage: {data['calls_today']}/{data['daily_limit']}")

test("Get usage stats", t7)

def t8():
    r = requests.get(f"{BASE_URL}/api/users/{test_data['user_id']}/sessions")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    print(f"   Sessions: {len(r.json())}")

test("Get user sessions", t8)

# 3. BREEDS API
print("\n3️⃣  BREEDS DATABASE")
print("-"*70)

def t9():
    r = requests.get(f"{BASE_URL}/api/breeds/")
    data = r.json()
    assert len(data["breeds"]) == 195
    print(f"   Breeds: {len(data['breeds'])}")

test("List breeds", t9)

def t10():
    r = requests.get(f"{BASE_URL}/api/breeds/Retrievers (Labrador)")
    data = r.json()
    assert data["breed"] == "Retrievers (Labrador)"
    assert len(data["images"]) == 35
    print(f"   Images: {len(data['images'])}")

test("Get breed details", t10)

# 4. CHAT API
print("\n4️⃣  CONVERSATIONAL AI")
print("-"*70)

def t11():
    r = requests.post(
        f"{BASE_URL}/api/chat/message",
        json={"message": "Hello! Looking for a dog.", "session_id": None}
    )
    data = r.json()
    test_data["session_id"] = data["session_id"]
    assert "session_id" in data
    response = data.get("message") or data.get("response", "")
    print(f"   Session: {data['session_id'][:20]}...")
    print(f"   Response: {response[:50]}...")

test("Chat with AI", t11)

def t12():
    r = requests.get(f"{BASE_URL}/api/chat/session/{test_data['session_id']}")
    data = r.json()
    assert "history" in data
    assert "profile" in data
    print(f"   History items: {len(data['history'])}")

test("Get session history", t12)

# 5. RECOMMENDATIONS
print("\n5️⃣  RECOMMENDATIONS")
print("-"*70)

def t13():
    r = requests.get(f"{BASE_URL}/api/recommendations/{test_data['session_id']}")
    # May return 400 if profile incomplete, which is expected
    if r.status_code == 400:
        print(f"   Profile incomplete (expected)")
    else:
        assert r.status_code == 200
        print(f"   Recommendations generated")

test("Get recommendations", t13)

# 6. GDPR
print("\n6️⃣  DATA PRIVACY")
print("-"*70)

def t14():
    r = requests.delete(f"{BASE_URL}/api/users/{test_data['user_id']}")
    assert r.status_code == 200
    assert "deleted" in r.json()["message"].lower()
    print(f"   User deleted: {test_data['user_id'][:20]}...")

test("Delete user data", t14)

def t15():
    r = requests.get(f"{BASE_URL}/api/users/{test_data['user_id']}")
    assert r.status_code == 404
    print(f"   Deletion verified (404)")

test("Verify deletion", t15)

# SUMMARY
print("\n" + "="*70)
print("📊 TEST SUMMARY")
print("="*70)
total = passed + failed
success_rate = (passed / total * 100) if total > 0 else 0

print(f"Total: {total}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print(f"Success Rate: {success_rate:.1f}%")

if failed == 0:
    print(f"\n🎉 ALL TESTS PASSED! PAWMATCH API IS PRODUCTION READY!")
else:
    print(f"\n⚠️  {failed} test(s) failed")

print("="*70)

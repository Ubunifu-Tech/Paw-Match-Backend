"""
User Features Test Suite

Tests user accounts, session persistence, rate limiting, and data deletion.

Usage:
    python tests/test_user_features.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.user_service import UserService
from app.services.session_service import SessionService
from app.services.gemini_service import GeminiService
from app.core.config import get_settings


class TestResults:
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


async def test_user_service():
    """Test UserService."""
    print("\n1️⃣  USER SERVICE TESTS")
    print("-" * 70)
    results = TestResults()
    
    service = UserService()
    
    # Test 1: Create anonymous user
    try:
        user = await service.create_anonymous_user()
        if user and user.is_anonymous:
            results.pass_test(f"Create anonymous user (ID: {str(user.id)[:8]}...)")
            test_user_id = user.id
        else:
            results.fail_test("Create anonymous user", "Invalid user")
            return results.summary()
    except Exception as e:
        results.fail_test("Create anonymous user", str(e))
        return results.summary()
    
    # Test 2: Get user
    try:
        user = await service.get_user(test_user_id)
        if user:
            results.pass_test("Get user by ID")
        else:
            results.fail_test("Get user by ID", "User not found")
    except Exception as e:
        results.fail_test("Get user by ID", str(e))
    
    # Test 3: Update preferences
    try:
        user = await service.update_preferences(test_user_id, {"theme": "dark"})
        if user and user.preferences.get("theme") == "dark":
            results.pass_test("Update preferences")
        else:
            results.fail_test("Update preferences", "Preferences not updated")
    except Exception as e:
        results.fail_test("Update preferences", str(e))
    
    # Test 4: Cross-session memory
    try:
        user = await service.update_memory(test_user_id, "favorite_breed", "Labrador")
        value = await service.get_memory(test_user_id, "favorite_breed")
        if value == "Labrador":
            results.pass_test("Cross-session memory")
        else:
            results.fail_test("Cross-session memory", f"Expected 'Labrador', got '{value}'")
    except Exception as e:
        results.fail_test("Cross-session memory", str(e))
    
    # Test 5: Rate limiting
    try:
        can_proceed, error = await service.check_rate_limit(test_user_id, "chat")
        if can_proceed:
            results.pass_test("Rate limiting check (allowed)")
        else:
            results.fail_test("Rate limiting check", error or "Blocked unexpectedly")
    except Exception as e:
        results.fail_test("Rate limiting check", str(e))
    
    # Test 6: API usage
    try:
        usage = await service.get_api_usage(test_user_id)
        if usage and "calls_today" in usage:
            results.pass_test(f"API usage tracking ({usage['calls_today']}/{usage['daily_limit']})")
        else:
            results.fail_test("API usage tracking", "Invalid usage data")
    except Exception as e:
        results.fail_test("API usage tracking", str(e))
    
    # Test 7: Register user
    try:
        new_user = await service.register_user("test@example.com", "TestUser")
        if new_user and not new_user.is_anonymous:
            results.pass_test(f"Register user ({new_user.email})")
            registered_user_id = new_user.id
        else:
            results.fail_test("Register user", "Registration failed")
            registered_user_id = None
    except Exception as e:
        results.fail_test("Register user", str(e))
        registered_user_id = None
    
    # Test 8: Delete user data
    try:
        deleted = await service.delete_user_data(test_user_id)
        if deleted:
            results.pass_test("Delete user data (anonymous)")
        else:
            results.fail_test("Delete user data", "Deletion failed")
    except Exception as e:
        results.fail_test("Delete user data", str(e))
    
    # Cleanup registered user
    if registered_user_id:
        try:
            await service.delete_user_data(registered_user_id)
        except:
            pass
    
    return results.summary()


async def test_session_service():
    """Test SessionService."""
    print("\n2️⃣  SESSION SERVICE TESTS")
    print("-" * 70)
    results = TestResults()
    
    user_service = UserService()
    session_service = SessionService()
    
    # Create test user
    user = await user_service.create_anonymous_user()
    
    # Test 1: Create session
    try:
        session = await session_service.create_session(user.id)
        if session:
            results.pass_test(f"Create session (ID: {str(session.id)[:8]}...)")
            test_session_id = session.id
        else:
            results.fail_test("Create session", "Session not created")
            return results.summary()
    except Exception as e:
        results.fail_test("Create session", str(e))
        return results.summary()
    
    # Test 2: Save message
    try:
        msg = await session_service.save_message(
            test_session_id,
            "user",
            "I want a family dog"
        )
        if msg:
            results.pass_test("Save message")
        else:
            results.fail_test("Save message", "Message not saved")
    except Exception as e:
        results.fail_test("Save message", str(e))
    
    # Test 3: Get messages
    try:
        messages = await session_service.get_messages(test_session_id)
        if len(messages) > 0 and hasattr(messages[0], 'created_at'):
            results.pass_test(f"Get messages ({len(messages)} messages)")
        else:
            results.fail_test("Get messages", "No messages found or invalid structure")
    except Exception as e:
        results.fail_test("Get messages", str(e))
    
    # Test 4: Update profile
    try:
        session = await session_service.update_profile(
            test_session_id,
            {"has_children": True}
        )
        if session and session.user_profile.get("has_children"):
            results.pass_test("Update profile")
        else:
            results.fail_test("Update profile", "Profile not updated")
    except Exception as e:
        results.fail_test("Update profile", str(e))
    
    # Test 5: Mark complete
    try:
        session = await session_service.mark_complete(test_session_id)
        if session and session.is_complete:
            results.pass_test("Mark session complete")
        else:
            results.fail_test("Mark session complete", "Not marked complete")
    except Exception as e:
        results.fail_test("Mark session complete", str(e))
    
    # Test 6: Conversation history
    try:
        history = await session_service.get_conversation_history(test_session_id)
        if history and "messages" in history:
            results.pass_test(f"Get conversation history ({len(history['messages'])} msgs)")
        else:
            results.fail_test("Get conversation history", "Invalid history")
    except Exception as e:
        results.fail_test("Get conversation history", str(e))
    
    # Test 7: Get user sessions
    try:
        sessions = await session_service.get_user_sessions(user.id)
        if len(sessions) > 0:
            results.pass_test(f"Get user sessions ({len(sessions)} sessions)")
        else:
            results.fail_test("Get user sessions", "No sessions found")
    except Exception as e:
        results.fail_test("Get user sessions", str(e))
    
    # Cleanup
    try:
        await user_service.delete_user_data(user.id)
    except:
        pass
    
    return results.summary()


def test_context_optimization():
    """Test context optimization."""
    print("\n3️⃣  CONTEXT OPTIMIZATION TESTS")
    print("-" * 70)
    results = TestResults()
    
    settings = get_settings()
    gemini = GeminiService(settings.gemini_api_key)
    
    # Test 1: Short conversation (no optimization)
    try:
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        summary, recent = gemini.optimize_context(messages)
        if summary is None and len(recent) == 2:
            results.pass_test("Short conversation (no optimization needed)")
        else:
            results.fail_test("Short conversation", "Unexpected optimization")
    except Exception as e:
        results.fail_test("Short conversation", str(e))
    
    # Test 2: Long conversation (optimization needed)
    try:
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(15)]
        summary, recent = gemini.optimize_context(messages, keep_recent=5)
        if summary and len(recent) == 5:
            results.pass_test(f"Long conversation (optimized: summary + {len(recent)} recent)")
        else:
            results.fail_test("Long conversation", f"Summary: {bool(summary)}, Recent: {len(recent)}")
    except Exception as e:
        results.fail_test("Long conversation", str(e))
    
    return results.summary()


async def run_all_tests():
    """Run all test suites."""
    print("\n" + "="*70)
    print("USER FEATURES TEST SUITE")
    print("="*70)
    
    all_passed = True
    
    # User service tests
    all_passed &= await test_user_service()
    
    # Session service tests
    all_passed &= await test_session_service()
    
    # Context optimization tests
    all_passed &= test_context_optimization()
    
    # Final summary
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL USER FEATURE TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*70)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

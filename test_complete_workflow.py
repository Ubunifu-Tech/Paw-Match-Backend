"""
Complete Workflow Test Script for PawMatch Backend

Tests the entire user journey from registration to video generation.
Run this after starting the backend server.

Usage:
    python test_complete_workflow.py
"""

import requests
import json
import time
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = f"test_user_{int(time.time())}@example.com"
TEST_PASSWORD = "Test1234"
TEST_USERNAME = "TestUser"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(step_num: int, description: str):
    """Print a test step header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}STEP {step_num}: {description}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")

def print_response(response: requests.Response):
    """Print formatted response"""
    print(f"{Colors.OKBLUE}Status Code: {response.status_code}{Colors.ENDC}")
    try:
        print(f"{Colors.OKBLUE}Response: {json.dumps(response.json(), indent=2)}{Colors.ENDC}")
    except:
        print(f"{Colors.OKBLUE}Response: {response.text}{Colors.ENDC}")

class WorkflowTester:
    def __init__(self):
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.recommendations = None
        
    def test_1_health_check(self):
        """Test 1: Health Check"""
        print_step(1, "Health Check")
        
        try:
            # Health check is at root, not under /api
            response = requests.get("http://localhost:8000/")
            print_response(response)
            
            if response.status_code == 200:
                print_success("Backend is running!")
                return True
            else:
                print_error("Backend health check failed")
                return False
        except Exception as e:
            print_error(f"Cannot connect to backend: {e}")
            print_info("Make sure the backend is running: uvicorn app.main:app --reload")
            return False
    
    def test_2_user_registration(self):
        """Test 2: User Registration"""
        print_step(2, "User Registration")
        
        payload = {
            "email": TEST_EMAIL,
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
        
        print_info(f"Registering user: {TEST_EMAIL}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/users/register",
                json=payload
            )
            print_response(response)
            
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get("user_id")
                print_success(f"User registered successfully! User ID: {self.user_id}")
                return True
            else:
                print_error("Registration failed")
                return False
        except Exception as e:
            print_error(f"Registration error: {e}")
            return False
    
    def test_3_password_validation(self):
        """Test 3: Password Validation"""
        print_step(3, "Password Validation (Weak Password)")
        
        weak_passwords = [
            ("password", "No uppercase or digit"),
            ("PASSWORD", "No lowercase or digit"),
            ("Pass123", "Less than 8 characters"),
            ("password123", "No uppercase")
        ]
        
        for weak_pwd, reason in weak_passwords:
            payload = {
                "email": f"weak_{int(time.time())}@example.com",
                "username": "WeakTest",
                "password": weak_pwd
            }
            
            print_info(f"Testing weak password: '{weak_pwd}' ({reason})")
            
            response = requests.post(
                f"{BASE_URL}/users/register",
                json=payload
            )
            
            if response.status_code == 400:
                print_success(f"Correctly rejected weak password: {response.json().get('detail')}")
            else:
                print_error(f"Should have rejected weak password but got: {response.status_code}")
        
        return True
    
    def test_4_login(self):
        """Test 4: User Login"""
        print_step(4, "User Login")
        
        payload = {
            "username": TEST_EMAIL,  # OAuth2 uses 'username' field for email
            "password": TEST_PASSWORD
        }
        
        print_info(f"Logging in as: {TEST_EMAIL}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/users/token",
                data=payload  # Note: form data, not JSON
            )
            print_response(response)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                print_success(f"Login successful! Token: {self.token[:20]}...")
                return True
            else:
                print_error("Login failed")
                return False
        except Exception as e:
            print_error(f"Login error: {e}")
            return False
    
    def test_5_get_user_profile(self):
        """Test 5: Get User Profile"""
        print_step(5, "Get User Profile (Protected Endpoint)")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(
                f"{BASE_URL}/users/me",
                headers=headers
            )
            print_response(response)
            
            if response.status_code == 200:
                print_success("Successfully retrieved user profile")
                return True
            else:
                print_error("Failed to get user profile")
                return False
        except Exception as e:
            print_error(f"Profile retrieval error: {e}")
            return False
    
    def test_6_start_conversation(self):
        """Test 6: Start Conversation"""
        print_step(6, "Start Conversation")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "message": "I want a family-friendly dog",
            "session_id": None
        }
        
        print_info("Sending first message to chatbot...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/chat/message",
                headers=headers,
                json=payload
            )
            print_response(response)
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
                print_success(f"Conversation started! Session ID: {self.session_id}")
                print_info(f"AI Response: {data.get('message')}")
                return True
            else:
                print_error("Failed to start conversation")
                return False
        except Exception as e:
            print_error(f"Conversation error: {e}")
            return False
    
    def test_7_continue_conversation(self):
        """Test 7: Continue Conversation"""
        print_step(7, "Continue Conversation")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Simulate a conversation
        messages = [
            "Yes, I have 2 kids ages 5 and 8",
            "We have a large fenced yard",
            "We're very active, we hike every weekend",
            "No allergies",
            "I'm a first-time dog owner",
            "I prefer medium to large dogs",
            "I can commit to daily training"
        ]
        
        for i, message in enumerate(messages, 1):
            print_info(f"Message {i}: {message}")
            
            payload = {
                "message": message,
                "session_id": self.session_id
            }
            
            try:
                response = requests.post(
                    f"{BASE_URL}/chat/message",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print_success(f"AI: {data.get('message')[:100]}...")
                    
                    if data.get("is_complete"):
                        print_success("Profile is complete!")
                        return True
                    
                    time.sleep(0.5)  # Brief pause between messages
                else:
                    print_error(f"Message {i} failed")
                    return False
            except Exception as e:
                print_error(f"Error sending message {i}: {e}")
                return False
        
        return True
    
    def test_8_get_recommendations(self):
        """Test 8: Get Breed Recommendations"""
        print_step(8, "Get Breed Recommendations")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        print_info(f"Getting recommendations for session: {self.session_id}")
        
        try:
            response = requests.get(
                f"{BASE_URL}/recommendations/{self.session_id}",
                headers=headers,
                params={"use_search": False}  # Disable web search for faster testing
            )
            print_response(response)
            
            if response.status_code == 200:
                data = response.json()
                self.recommendations = data.get("top_three", [])
                
                print_success(f"Got {len(self.recommendations)} breed recommendations!")
                
                for i, rec in enumerate(self.recommendations, 1):
                    breed = rec.get("breed", {})
                    print_info(f"\n#{i}: {breed.get('breed')} - Match Score: {rec.get('match_score')}%")
                    print_info(f"   Pros: {', '.join(rec.get('pros', [])[:3])}")
                    print_info(f"   Cons: {', '.join(rec.get('cons', [])[:3])}")
                
                return True
            else:
                print_error("Failed to get recommendations")
                return False
        except Exception as e:
            print_error(f"Recommendations error: {e}")
            return False
    
    def test_9_get_session_history(self):
        """Test 9: Get Session History"""
        print_step(9, "Get Session History")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(
                f"{BASE_URL}/users/me/sessions",
                headers=headers
            )
            print_response(response)
            
            if response.status_code == 200:
                sessions = response.json()
                print_success(f"Retrieved {len(sessions)} session(s)")
                return True
            else:
                print_error("Failed to get session history")
                return False
        except Exception as e:
            print_error(f"Session history error: {e}")
            return False
    
    def test_10_api_usage(self):
        """Test 10: Check API Usage"""
        print_step(10, "Check API Usage")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(
                f"{BASE_URL}/users/me/usage",
                headers=headers
            )
            print_response(response)
            
            if response.status_code == 200:
                usage = response.json()
                print_success(f"API Usage: {usage.get('calls_today')}/{usage.get('daily_limit')}")
                print_info(f"Remaining: {usage.get('remaining')} calls")
                return True
            else:
                print_error("Failed to get API usage")
                return False
        except Exception as e:
            print_error(f"API usage error: {e}")
            return False
    
    def test_11_unauthorized_access(self):
        """Test 11: Test Unauthorized Access"""
        print_step(11, "Test Unauthorized Access (Security)")
        
        # Try to access protected endpoint without token
        print_info("Attempting to access /users/me without token...")
        
        response = requests.get(f"{BASE_URL}/users/me")
        
        if response.status_code == 401:
            print_success("Correctly rejected unauthorized request")
        else:
            print_error(f"Should have returned 401, got {response.status_code}")
            return False
        
        # Try with invalid token
        print_info("Attempting to access with invalid token...")
        
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = requests.get(f"{BASE_URL}/users/me", headers=headers)
        
        if response.status_code == 401:
            print_success("Correctly rejected invalid token")
            return True
        else:
            print_error(f"Should have returned 401, got {response.status_code}")
            return False
    
    def test_12_session_ownership(self):
        """Test 12: Test Session Ownership (Authorization)"""
        print_step(12, "Test Session Ownership (Authorization)")
        
        # Create another user
        other_email = f"other_user_{int(time.time())}@example.com"
        payload = {
            "email": other_email,
            "username": "OtherUser",
            "password": "Other1234"
        }
        
        print_info(f"Creating second user: {other_email}")
        
        response = requests.post(f"{BASE_URL}/users/register", json=payload)
        
        if response.status_code != 200:
            print_error("Failed to create second user")
            return False
        
        # Login as second user
        login_payload = {"username": other_email, "password": "Other1234"}
        response = requests.post(f"{BASE_URL}/users/token", data=login_payload)
        
        if response.status_code != 200:
            print_error("Failed to login as second user")
            return False
        
        other_token = response.json().get("access_token")
        
        # Try to access first user's session
        print_info(f"Attempting to access first user's session with second user's token...")
        
        headers = {"Authorization": f"Bearer {other_token}"}
        response = requests.get(
            f"{BASE_URL}/recommendations/{self.session_id}",
            headers=headers
        )
        
        if response.status_code == 403:
            print_success("Correctly rejected unauthorized session access (403 Forbidden)")
            return True
        else:
            print_error(f"Should have returned 403, got {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run all workflow tests"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("="*70)
        print("  PAWMATCH BACKEND - COMPLETE WORKFLOW TEST")
        print("="*70)
        print(f"{Colors.ENDC}\n")
        
        tests = [
            self.test_1_health_check,
            self.test_2_user_registration,
            self.test_3_password_validation,
            self.test_4_login,
            self.test_5_get_user_profile,
            self.test_6_start_conversation,
            self.test_7_continue_conversation,
            self.test_8_get_recommendations,
            self.test_9_get_session_history,
            self.test_10_api_usage,
            self.test_11_unauthorized_access,
            self.test_12_session_ownership,
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
                    print_error(f"{test.__doc__} FAILED")
            except Exception as e:
                failed += 1
                print_error(f"{test.__doc__} CRASHED: {e}")
        
        # Summary
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("="*70)
        print("  TEST SUMMARY")
        print("="*70)
        print(f"{Colors.ENDC}")
        
        total = passed + failed
        print(f"\nTotal Tests: {total}")
        print(f"{Colors.OKGREEN}Passed: {passed}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {failed}{Colors.ENDC}")
        
        if failed == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ ALL TESTS PASSED! Backend is working correctly.{Colors.ENDC}\n")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}✗ Some tests failed. Please review the errors above.{Colors.ENDC}\n")
        
        return failed == 0

if __name__ == "__main__":
    tester = WorkflowTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)


import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_unauthenticated_user_access():
    """
    Tests that an unauthenticated user cannot access protected endpoints.
    This test should fail initially, and then pass after authentication is implemented.
    """
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    # Attempt to access protected endpoints without authentication
    response = client.get(f"/api/users/{user_id}")
    assert response.status_code == 401, "Should require authentication"

    response = client.get(f"/api/chat/session/{session_id}")
    assert response.status_code == 401, "Should require authentication"

    response = client.get(f"/api/recommendations/{session_id}")
    assert response.status_code == 401, "Should require authentication"

def test_unauthorized_user_access():
    """
    Tests that a user cannot access the data of another user.
    This test should fail initially, and then pass after authorization is implemented.
    """
    # Create two users
    user_1_id = client.post("/api/users/anonymous").json()["user_id"]
    user_2_id = client.post("/api/users/anonymous").json()["user_id"]

    # User 1 creates a session
    response = client.post("/api/chat/message", json={"session_id": None, "message": "hello"})
    session_id = response.json()["session_id"]

    # User 2 should not be able to access user 1's session
    response = client.get(f"/api/chat/session/{session_id}", headers={"Authorization": f"Bearer {user_2_id}"})
    assert response.status_code == 403, "Should be forbidden"

    # User 2 should not be able to access user 1's data
    response = client.get(f"/api/users/{user_1_id}", headers={"Authorization": f"Bearer {user_2_id}"})
    assert response.status_code == 403, "Should be forbidden"

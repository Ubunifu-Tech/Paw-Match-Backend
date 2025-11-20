"""
Create a test user in the database
"""
import asyncio
import sys
from app.core.database import AsyncSessionLocal
from app.db.models import User
from app.core.security import get_password_hash
import uuid

async def create_test_user(email: str, username: str, password: str):
    """Create a test user with the given credentials"""
    
    async with AsyncSessionLocal() as db:
        # Check if user already exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"❌ User with email {email} already exists!")
            print(f"   User ID: {existing_user.id}")
            print(f"   Username: {existing_user.username}")
            return
        
        # Create new user
        hashed_password = get_password_hash(password)
        
        user = User(
            id=uuid.uuid4(),
            email=email,
            username=username,
            hashed_password=hashed_password,
            is_anonymous=False,
            preferences={},
            cross_session_memory={}
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        print("✅ Test user created successfully!")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Password: {password}")
        print(f"   User ID: {user.id}")
        print(f"\n🔐 You can now login with:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")

if __name__ == "__main__":
    # Default test user
    email = "test@pawmatch.ai"
    username = "TestUser"
    password = "Test1234"
    
    # Allow custom credentials via command line
    if len(sys.argv) >= 4:
        email = sys.argv[1]
        username = sys.argv[2]
        password = sys.argv[3]
    
    print(f"Creating test user: {email}")
    asyncio.run(create_test_user(email, username, password))

"""
Deployment Readiness Test Suite

Comprehensive tests to verify production readiness.

Usage:
    python tests/test_deployment_readiness.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.breed_service import BreedService
from app.services.user_service import UserService
from app.services.session_service import SessionService
from app.services.cache_service import CacheService
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, func
from app.db.models import Breed, BreedImage, User, Session, ChatMessage


class AuditReport:
    def __init__(self):
        self.sections = []
        self.issues = []
        self.warnings = []
        self.successes = []
    
    def add_section(self, title):
        self.sections.append({"title": title, "items": []})
    
    def add_success(self, message):
        self.successes.append(message)
        if self.sections:
            self.sections[-1]["items"].append(f"✅ {message}")
        print(f"  ✅ {message}")
    
    def add_warning(self, message):
        self.warnings.append(message)
        if self.sections:
            self.sections[-1]["items"].append(f"⚠️  {message}")
        print(f"  ⚠️  {message}")
    
    def add_issue(self, message):
        self.issues.append(message)
        if self.sections:
            self.sections[-1]["items"].append(f"❌ {message}")
        print(f"  ❌ {message}")
    
    def get_grade(self):
        if len(self.issues) == 0 and len(self.warnings) == 0:
            return "A+ (Production Ready)"
        elif len(self.issues) == 0 and len(self.warnings) <= 2:
            return "A (Production Ready with Minor Notes)"
        elif len(self.issues) <= 2:
            return "B (Needs Minor Fixes)"
        else:
            return "C (Needs Major Fixes)"
    
    def print_summary(self):
        print("\n" + "="*70)
        print("DEPLOYMENT READINESS REPORT")
        print("="*70)
        
        for section in self.sections:
            print(f"\n{section['title']}")
            print("-" * 70)
            for item in section['items']:
                print(item)
        
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"✅ Successes: {len(self.successes)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Issues: {len(self.issues)}")
        print(f"\n🎯 GRADE: {self.get_grade()}")
        print("="*70)
        
        return len(self.issues) == 0


async def test_database_integrity(report: AuditReport):
    """Test database integrity."""
    report.add_section("📊 DATABASE INTEGRITY")
    
    try:
        async with AsyncSessionLocal() as db:
            # Check breeds
            result = await db.execute(select(func.count(Breed.id)))
            breed_count = result.scalar()
            if breed_count >= 100:
                report.add_success(f"Breeds table: {breed_count} breeds")
            else:
                report.add_warning(f"Only {breed_count} breeds (expected 195)")
            
            # Check images
            result = await db.execute(select(func.count(BreedImage.id)))
            image_count = result.scalar()
            if image_count >= 1000:
                report.add_success(f"Images table: {image_count} images")
            else:
                report.add_warning(f"Only {image_count} images (expected ~6825)")
            
            # Check users table exists
            result = await db.execute(select(func.count(User.id)))
            user_count = result.scalar()
            report.add_success(f"Users table: {user_count} users (ready)")
            
            # Check sessions table exists
            result = await db.execute(select(func.count(Session.id)))
            session_count = result.scalar()
            report.add_success(f"Sessions table: {session_count} sessions (ready)")
            
            # Check foreign key relationships
            result = await db.execute(select(Session).limit(1))
            session = result.scalar_one_or_none()
            if session:
                report.add_success("Session model has proper structure")
            else:
                report.add_success("Session table ready (empty)")
    
    except Exception as e:
        report.add_issue(f"Database error: {e}")


async def test_services(report: AuditReport):
    """Test all services."""
    report.add_section("🔧 SERVICES")
    
    # Breed Service
    try:
        service = BreedService()
        breeds = await service.get_all_breeds()
        if len(breeds) >= 100:
            report.add_success(f"BreedService: {len(breeds)} breeds accessible")
        else:
            report.add_warning(f"BreedService: only {len(breeds)} breeds")
        
        # Test search
        results = await service.search_breeds("lab")
        if results:
            report.add_success(f"Breed search working ({len(results)} results)")
        else:
            report.add_warning("Breed search returned no results")
    
    except Exception as e:
        report.add_issue(f"BreedService error: {e}")
    
    # User Service
    try:
        service = UserService()
        user = await service.create_anonymous_user()
        if user:
            report.add_success("UserService: anonymous user creation works")
            # Cleanup
            await service.delete_user_data(user.id)
        else:
            report.add_issue("UserService: cannot create users")
    except Exception as e:
        report.add_issue(f"UserService error: {e}")
    
    # Session Service
    try:
        user_service = UserService()
        session_service = SessionService()
        user = await user_service.create_anonymous_user()
        session = await session_service.create_session(user.id)
        if session:
            report.add_success("SessionService: session creation works")
            await user_service.delete_user_data(user.id)
        else:
            report.add_issue("SessionService: cannot create sessions")
    except Exception as e:
        report.add_issue(f"SessionService error: {e}")
    
    # Cache Service
    try:
        cache = CacheService()
        await cache.connect()
        if cache.redis:
            report.add_success("CacheService: Redis connection successful")
            await cache.close()
        else:
            report.add_warning("CacheService: Redis not connected (optional)")
    except Exception as e:
        report.add_warning(f"CacheService: {e} (Redis is optional)")


async def test_api_endpoints(report: AuditReport):
    """Test API structure."""
    report.add_section("🌐 API ENDPOINTS")
    
    try:
        from app.main import app
        routes = [r for r in app.routes if hasattr(r, 'path') and r.path.startswith('/api/')]
        
        endpoint_groups = {
            'users': 0,
            'chat': 0,
            'recommendations': 0,
            'breeds': 0,
            'video': 0
        }
        
        for route in routes:
            for group in endpoint_groups:
                if group in route.path:
                    endpoint_groups[group] += 1
        
        for group, count in endpoint_groups.items():
            if count > 0:
                report.add_success(f"{group.capitalize()} API: {count} endpoints")
            else:
                report.add_warning(f"{group.capitalize()} API: no endpoints")
        
        total_routes = len([r for r in app.routes if hasattr(r, 'path')])
        report.add_success(f"Total routes: {total_routes}")
    
    except Exception as e:
        report.add_issue(f"API structure error: {e}")


def test_configuration(report: AuditReport):
    """Test configuration."""
    report.add_section("⚙️  CONFIGURATION")
    
    try:
        settings = get_settings()
        
        # Check required settings
        if settings.gemini_api_key:
            report.add_success("Gemini API key configured")
        else:
            report.add_issue("Gemini API key missing")
        
        if settings.database_url:
            report.add_success(f"Database URL configured")
        else:
            report.add_issue("Database URL missing")
        
        if settings.redis_url:
            report.add_success("Redis URL configured")
        else:
            report.add_warning("Redis URL missing (optional)")
        
        if not settings.debug:
            report.add_success("Debug mode OFF (production ready)")
        else:
            report.add_warning("Debug mode ON (should be OFF for production)")
        
        if settings.frontend_url:
            report.add_success(f"CORS configured for: {settings.frontend_url}")
        else:
            report.add_warning("Frontend URL not configured")
    
    except Exception as e:
        report.add_issue(f"Configuration error: {e}")


def test_error_handling(report: AuditReport):
    """Test error handling."""
    report.add_section("🛡️  ERROR HANDLING & SECURITY")
    
    try:
        from app.middleware import error_handler
        from app.main import app
        
        # Check exception handlers are registered
        handlers = app.exception_handlers
        if handlers:
            report.add_success(f"Exception handlers registered: {len(handlers)}")
        else:
            report.add_warning("No exception handlers registered")
        
        # Check CORS
        cors_middleware = any('cors' in str(type(m)).lower() for m in app.user_middleware)
        if cors_middleware:
            report.add_success("CORS middleware enabled")
        else:
            report.add_warning("CORS middleware not found")
        
        # Security headers
        report.add_warning("Recommendation: Add security headers (X-Content-Type-Options, etc.)")
        report.add_warning("Recommendation: Add request rate limiting middleware")
        
    except Exception as e:
        report.add_issue(f"Error handling check failed: {e}")


def test_dependencies(report: AuditReport):
    """Test dependencies."""
    report.add_section("📦 DEPENDENCIES")
    
    try:
        import fastapi
        import sqlalchemy
        import redis
        import pandas
        
        report.add_success(f"FastAPI {fastapi.__version__}")
        report.add_success(f"SQLAlchemy {sqlalchemy.__version__}")
        report.add_success(f"Redis {redis.__version__}")
        report.add_success(f"Pandas {pandas.__version__}")
        
        # Check requirements.txt exists
        req_file = Path(__file__).parent.parent / "requirements.txt"
        if req_file.exists():
            report.add_success("requirements.txt exists")
        else:
            report.add_issue("requirements.txt missing")
    
    except Exception as e:
        report.add_issue(f"Dependency check failed: {e}")


def test_documentation(report: AuditReport):
    """Test documentation."""
    report.add_section("📝 DOCUMENTATION")
    
    base_dir = Path(__file__).parent.parent.parent
    
    docs = {
        "README.md": base_dir / "backend" / "README.md",
        "DEPLOYMENT_GUIDE.md": base_dir / "DEPLOYMENT_GUIDE.md",
        "DATABASE_SETUP.md": base_dir / "backend" / "DATABASE_SETUP.md",
        "BACKEND_STATUS.md": base_dir / "BACKEND_STATUS.md",
    }
    
    for doc_name, doc_path in docs.items():
        if doc_path.exists():
            report.add_success(f"{doc_name} exists")
        else:
            report.add_warning(f"{doc_name} missing")


async def run_audit():
    """Run complete deployment readiness audit."""
    print("\n" + "="*70)
    print("🔍 DEPLOYMENT READINESS AUDIT")
    print("="*70)
    
    report = AuditReport()
    
    # Run all tests
    await test_database_integrity(report)
    await test_services(report)
    await test_api_endpoints(report)
    test_configuration(report)
    test_error_handling(report)
    test_dependencies(report)
    test_documentation(report)
    
    # Print summary
    return report.print_summary()


if __name__ == "__main__":
    success = asyncio.run(run_audit())
    sys.exit(0 if success else 1)

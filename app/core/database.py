"""
Database Configuration Module

Configures SQLAlchemy for PostgreSQL database connections with async support.
Provides session management and base model class for all database models.

Author: PawMatch Team
Version: 1.0.0
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for all models
Base = declarative_base()


async def get_db():
    """
    Dependency for getting database sessions.
    
    Yields an async database session and ensures proper cleanup.
    Use this as a FastAPI dependency for database access.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        >>> @router.get("/users")
        >>> async def get_users(db: AsyncSession = Depends(get_db)):
        >>>     result = await db.execute(select(User))
        >>>     return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database by creating all tables.
    
    Creates all tables defined in models if they don't exist.
    Should be called on application startup.
    
    Example:
        >>> await init_db()
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Close database connections.
    
    Disposes of the engine and closes all connections.
    Should be called on application shutdown.
    
    Example:
        >>> await close_db()
    """
    await engine.dispose()

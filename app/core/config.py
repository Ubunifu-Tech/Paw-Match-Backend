from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    # API Settings
    app_name: str = "PawMatch"
    api_version: str = "v1"
    debug: bool = False

    # AI API Key (Gemini only)
    gemini_api_key: str

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/dogmatch"
    
    @field_validator("database_url", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        """Convert Railway/Heroku DATABASE_URL to asyncpg format"""
        if v:
            # Handle postgres:// (Railway default)
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            # Handle postgresql:// (without asyncpg)
            elif v.startswith("postgresql://") and "+asyncpg" not in v:
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # CORS
    frontend_url: str = "http://localhost:3000"

    data_dir: str = "app/data"
    image_dir: str = "app/data/images"

    # Security - MUST be set in environment variables
    secret_key: str  # No default - must be provided via .env
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
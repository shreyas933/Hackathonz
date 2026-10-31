import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Brightloop Subscription Management System"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "brightloop_super_secret_dev_key_change_in_production_987654321")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Defaults to local SQLite file for immediate sandbox execution, supports PostgreSQL via DATABASE_URL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./brightloop.db")
    
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_CURRENCY_SYMBOL: str = "₹"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()


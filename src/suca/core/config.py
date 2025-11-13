"""Application configuration settings."""

import os
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseModel):
    """Application settings."""
    
    # Database - PostgreSQL configuration
    @property
    def database_url(self) -> str:
        """Construct database URL from environment variables."""
        # Check if DATABASE_URL is explicitly set
        explicit_url = os.getenv("DATABASE_URL")
        if explicit_url:
            return explicit_url
        
        # Build PostgreSQL URL from individual components
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASS", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "suca")
        
        return f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    # API
    api_title: str = os.getenv("API_TITLE", "SUCA API")
    api_version: str = os.getenv("API_VERSION", "1.0.0")
    api_description: str = os.getenv("API_DESCRIPTION", "SUCA Dictionary API")
    
    # CORS
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173", 
    ]
    
    # Debug
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"


# Global settings instance
settings = Settings()
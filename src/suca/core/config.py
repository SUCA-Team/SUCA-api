"""Application configuration settings."""

import os

from dotenv import load_dotenv
from pydantic import BaseModel

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
        db_user = os.getenv("DB_USER", "suca")
        db_pass = os.getenv("DB_PASS", "suca")
        db_host = os.getenv("DB_HOST", "db")
        db_port = os.getenv("DB_PORT", "5433")
        db_name = os.getenv("DB_NAME", "jmdict")

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

    # JWT Authentication
    @property
    def jwt_secret_key(self) -> str:
        """Get JWT secret key. Raise error if not set in production."""
        secret = os.getenv("JWT_SECRET_KEY")

        if not secret:
            if not self.debug:
                raise ValueError(
                    "JWT_SECRET_KEY must be set in production! "
                    "Generate one with: openssl rand -hex 32"
                )
            # Development fallback
            return "dev-secret-key-DO-NOT-USE-IN-PRODUCTION"

        return secret


# Global settings instance
settings = Settings()

"""Environment variable validators."""

import os


def validate_required_env_vars() -> None:
    """Validate that all required environment variables are set."""
    required_vars = {
        "DB_HOST": "Database host",
        "DB_PORT": "Database port",
        "DB_USER": "Database user",
        "DB_PASS": "Database password",
        "DB_NAME": "Database name",
    }

    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({description})")

    # Only enforce in production
    if missing and os.getenv("ENV", "dev") == "prod":
        raise ValueError(
            "Missing required environment variables:\n" + "\n".join(f"  - {m}" for m in missing)
        )


def validate_jwt_secret() -> None:
    """Validate JWT secret key."""
    secret = os.getenv("JWT_SECRET_KEY")

    # Only enforce in production
    if not secret and os.getenv("ENV", "dev") == "prod":
        raise ValueError(
            "JWT_SECRET_KEY must be set in production!\nGenerate one with: openssl rand -hex 32"
        )

    # Check length if secret is provided
    if secret and len(secret) < 32:
        raise ValueError("JWT_SECRET_KEY must be at least 32 characters long for security")

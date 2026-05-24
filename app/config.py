# Configuration module for application-wide settings such as database URI, API credentials, and environment variables.

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Inherits from:
        BaseSettings (pydantic_settings.BaseSettings): Automatically loads values from environment variables.
    """

    # Bearer token used for internal service authentication
    BEARER_TOKEN: str

    # Secret key for signing and verifying JWT tokens
    JWT_SECRET: str

    # MongoDB connection URI
    MONGO_URI: str

    # Name of the MongoDB database to connect to
    DB_NAME: str

    # PostgreSQL connection URI (optional; used when migrating to PostgreSQL)
    POSTGRES_URI: str | None = None
    DATABASE_URL: str | None = None

    # PostgreSQL database name
    POSTGRES_DB: str | None = None

    # PostgreSQL host
    POSTGRES_HOST: str | None = None

    # PostgreSQL port
    POSTGRES_PORT: int | None = None

    # PostgreSQL user
    POSTGRES_USER: str | None = None

    # PostgreSQL password
    POSTGRES_PASSWORD: str | None = None

    # PostgreSQL SSL mode
    PGSSLMODE: str | None = None

    # Base domain URL of the application (e.g., for CORS, redirects)
    DOMAIN_URL: str

    # Google OAuth 2.0 client ID for authentication
    GOOGLE_CLIENT_ID: str

    # Google OAuth 2.0 client secret for authentication
    GOOGLE_CLIENT_SECRET: str

    # Algorithm used for encoding JWT tokens
    JWT_ALGORITHM: str = "HS256"

    # Access token expiration time in minutes (default: 12 hours)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720

    # Guest token expiration time in minutes (default: 4 hours)
    GUEST_TOKEN_EXPIRE_MINUTES: int = 240

    # Refresh token expiration time in minutes (default: 7 days)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080

    class Config:
        # Path to the .env file from which to load environment variables
        env_file = ".env"

# Instantiate the settings object to be used throughout the application
settings = Settings()

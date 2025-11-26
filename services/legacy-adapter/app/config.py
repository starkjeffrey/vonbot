"""Configuration from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment.

    All settings can be overridden via environment variables.
    Sensitive values (passwords, API keys) must be set via .env file.
    """

    # Legacy MSSQL database connection
    LEGACY_DB_HOST: str
    LEGACY_DB_PORT: int = 1433
    LEGACY_DB_USER: str
    LEGACY_DB_PASSWORD: str
    LEGACY_DB_NAME: str

    # Security settings
    API_KEY: str
    ALLOWED_ORIGINS: str = "http://localhost:8000"
    ALLOWED_HOSTS: str = "legacy-adapter.vps.example.com,localhost"
    RATE_LIMIT_PER_MINUTE: int = 60

    # Application settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # API server settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()

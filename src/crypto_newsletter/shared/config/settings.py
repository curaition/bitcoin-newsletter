"""Application settings and configuration."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=[".env.development", ".env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    railway_environment: str = Field(default="development", alias="RAILWAY_ENVIRONMENT")
    service_type: str = Field(default="web", alias="SERVICE_TYPE")
    debug: bool = Field(default=True, alias="DEBUG")
    testing: bool = Field(default=False, alias="TESTING")

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # CoinDesk API
    coindesk_api_key: str = Field(..., alias="COINDESK_API_KEY")
    coindesk_base_url: str = Field(
        default="https://data-api.coindesk.com", alias="COINDESK_BASE_URL"
    )

    # Article Processing
    article_retention_hours: int = Field(default=24, alias="ARTICLE_RETENTION_HOURS")
    ingestion_schedule_hours: int = Field(default=4, alias="INGESTION_SCHEDULE_HOURS")

    # AI/ML
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    pydantic_ai_model: str = Field(
        default="gemini-1.5-flash", alias="PYDANTIC_AI_MODEL"
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # Email
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    from_email: Optional[str] = Field(default=None, alias="FROM_EMAIL")

    # Celery
    enable_celery: bool = Field(default=False, alias="ENABLE_CELERY")
    celery_broker_url: Optional[str] = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: Optional[str] = Field(
        default=None, alias="CELERY_RESULT_BACKEND"
    )

    # Security
    secret_key: str = Field(default="dev-secret-key", alias="SECRET_KEY")

    # Railway specific (automatically set in Railway)
    railway_project_id: Optional[str] = Field(default=None, alias="RAILWAY_PROJECT_ID")
    railway_service_id: Optional[str] = Field(default=None, alias="RAILWAY_SERVICE_ID")
    railway_deployment_id: Optional[str] = Field(
        default=None, alias="RAILWAY_DEPLOYMENT_ID"
    )
    railway_public_domain: Optional[str] = Field(
        default=None, alias="RAILWAY_PUBLIC_DOMAIN"
    )
    railway_private_domain: Optional[str] = Field(
        default=None, alias="RAILWAY_PRIVATE_DOMAIN"
    )
    port: int = Field(default=8000, alias="PORT")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.railway_environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.railway_environment == "development"

    @property
    def effective_celery_broker_url(self) -> str:
        """Get effective Celery broker URL."""
        return self.celery_broker_url or self.redis_url

    @property
    def effective_celery_result_backend(self) -> str:
        """Get effective Celery result backend URL."""
        return self.celery_result_backend or self.redis_url


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings singleton (useful for testing)."""
    global _settings
    _settings = None

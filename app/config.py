"""
Configuration management using Pydantic settings.
Loads and validates environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Slack Configuration
    slack_bot_token: str
    slack_signing_secret: str  # Signing secret for webhook verification
    
    # Gemini AI Configuration
    gemini_api_key: str
    
    # SashiDo Configuration
    sashido_app_id: str
    sashido_rest_key: str
    sashido_api_url: str
    
    # Application Configuration
    environment: str = "development"
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global settings
    if settings is None:
        settings = Settings()
    return settings


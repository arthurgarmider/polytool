"""Configuration for PolyTool."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """PolyTool configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="POLYTOOL_",
        env_file=".env",
        extra="ignore",
    )
    
    # Default LLM settings
    default_model: str = "gpt-4o"
    default_temperature: float = 0.0
    default_max_tokens: int = 4096
    
    # Sandbox settings
    sandbox_type: Literal["e2b", "restricted", "docker"] = "e2b"
    sandbox_timeout_seconds: int = 60
    
    # E2B settings
    e2b_api_key: str | None = None
    
    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    # Logging
    log_level: str = "INFO"
    log_tool_calls: bool = True
    log_generated_code: bool = True
    
    # Cost tracking
    track_costs: bool = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()



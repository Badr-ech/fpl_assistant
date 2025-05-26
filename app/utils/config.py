import os
from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional
class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Subscription Tiers and Model Configuration
    SUBSCRIPTION_TIERS: Dict[str, Dict[str, Any]] = {
        "basic": {
            "model_version": "basic-v1",
            "recommendations_limit": 3,
            "captain_picks_limit": 2,
        },
        "premium": {
            "model_version": "premium-v1",
            "recommendations_limit": 5,
            "captain_picks_limit": 3,
        },
        "elite": {
            "model_version": "elite-v1",
            "recommendations_limit": 10,
            "captain_picks_limit": 5,
        }
    }
    
    # FPL API Timeouts
    FPL_API_TIMEOUT: float = 30.0
    # Model Path (for local AI models)
    MODEL_PATH: Optional[str] = None
    # Telegram Bot and API URL (add these to avoid pydantic extra_forbidden error)
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    FPL_ASSISTANT_API_URL: Optional[str] = None
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# Create global settings object
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings
    """
    return settings

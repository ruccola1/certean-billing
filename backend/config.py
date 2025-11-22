from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    mongodb_uri: str = ""  # Will be set from env
    mongodb_db_name: str = "c_monitor_shared"
    
    # Stripe Configuration
    stripe_secret_key: str = ""  # Will be set from env
    frontend_url: str = "http://localhost:5173"
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8001  # Different port from certean-ai
    
    # Authentication (Optional)
    api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


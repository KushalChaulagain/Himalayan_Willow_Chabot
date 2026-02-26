from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application configuration with environment variable validation"""
    
    # LLM Configuration
    gemini_api_key: str
    groq_api_key: str = ""  # Fallback LLM; leave empty to disable Groq fallback
    
    # Database (optional: leave empty to run without PostgreSQL; chat will work, orders/persistence will return 503)
    database_url: str = ""
    
    # Payment Gateways
    esewa_merchant_id: str = ""
    esewa_secret_key: str = ""
    esewa_base_url: str = "https://uat.esewa.com.np"
    khalti_secret_key: str = ""
    khalti_base_url: str = "https://khalti.com"
    
    # Notifications
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    resend_api_key: str = ""
    
    # Auth (Google OAuth)
    google_client_id: str = ""  # OAuth 2.0 Web client ID from Google Cloud Console

    # Application
    base_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    jwt_secret: str
    environment: str = "development"
    
    # Store Configuration
    store_id: int = 1
    store_name: str = "Himalayan Willow"
    store_maps_url: str = "https://maps.app.goo.gl/WiWrohWFkAWWHput8"
    store_phone: str = ""
    
    # Monitoring & Observability
    sentry_dsn: str = ""  # Optional: Sentry DSN for error tracking
    enable_sentry: bool = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

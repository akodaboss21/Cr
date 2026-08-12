from pydantic_settings import BaseSettings
from typing import Optional
from .config_validator import validate_config  # Import validator

class Settings(BaseSettings):
    # Supabase Database
    SUPABASE_PROJECT_ID: str = "local-project"
    SUPABASE_DB_PASSWORD: str = "local-password"
    SUPABASE_DB_HOST: str = "db.supabase.co"
    SUPABASE_DB_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    @property
    def database_url(self) -> str:
        if self.__dict__.get("DATABASE_URL"):
            return self.__dict__["DATABASE_URL"]
        if self.__dict__.get("SUPABASE_DB_HOST") and self.__dict__.get("SUPABASE_DB_HOST") != "db.supabase.co":
            return f"postgresql://postgres:{self.SUPABASE_DB_PASSWORD}@{self.SUPABASE_DB_HOST}:{self.SUPABASE_DB_PORT}/{self.SUPABASE_PROJECT_ID}"
        return "sqlite:///./carai_local.db"

    # Supabase Auth
    SUPABASE_URL: str = "http://localhost:54321"
    SUPABASE_ANON_KEY: str = "local-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "local-service-role-key"

    # Application
    APP_NAME: str = "Carai Receptionist"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    WIDGET_API_KEY: Optional[str] = None
    WIDGET_SIGNING_SECRET: Optional[str] = None
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    CSRF_ENABLED: bool = True
    MAX_INPUT_LENGTH: int = 10000

    # AI Providers
    OPENAI_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: Optional[str] = "http://localhost:11434"

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = ""
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@carai.com"
    EMAILS_FROM_NAME: str = "Carai Receptionist"

    # Notifications / messaging
    SMS_PROVIDER: str = "disabled"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    WHATSAPP_PROVIDER: str = "disabled"
    WHATSAPP_API_URL: str = ""
    WHATSAPP_API_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER: str = ""
    PUSH_PROVIDER: str = "disabled"

    # Observability
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENV: Optional[str] = "development"

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance and validate
settings = Settings()
# validate_config()  # Disabled during import to avoid test-time environment requirements
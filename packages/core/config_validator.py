from pydantic import ValidationError
from pydantic_settings import BaseSettings
from typing import Dict, Any
import os
import sys

class ConfigValidator(BaseSettings):
    """Configuration validator that ensures required environment variables are present."""
    
    # Required environment variables
    REQUIRED_VARS: Dict[str, str] = {
        "DATABASE_URL": "Database Connection String",
        "SUPABASE_URL": "Supabase Client URL",
        "SUPABASE_ANON_KEY": "Supabase Anon Key",
        "SUPABASE_SERVICE_ROLE_KEY": "Supabase Service Role Key",
        "SECRET_KEY": "Application Secret Key",
        "JWT_SECRET": "JWT Signing Secret",
        "OPENAI_API_KEY": "OpenAI API Key",
        "OLLAMA_BASE_URL": "Local LLM Base URL",
        "STRIPE_SECRET_KEY": "Stripe Secret Key",
        "SMTP_HOST": "SMTP Host",
        "SMTP_PORT": "SMTP Port",
        "SMTP_USER": "SMTP User",
        "SMTP_PASSWORD": "SMTP Password",
        "ALLOWED_ORIGINS": "Allowed Origins",
        "API_ENDPOINT": "API Endpoint URL",
        "MAX_CONNECTIONS": "Maximum Database Connections",
    }
    
    # Optional but recommended variables
    RECOMMENDED_VARS: Dict[str, str] = {
        "REDIS_URL": "Redis URL",
        "SMTP_PASSWORD": "SMTP Password",
        "SMTP_USER": "SMTP User",
        "SMTP_HOST": "SMTP Host",
        "SMTP_TLS": "SMTP TLS Setting",
        "APP_NAME": "Application Name",
        "APP_VERSION": "Application Version",
    }
    
    def validate_required_vars(self) -> None:
        """Validate that all required environment variables are present."""
        missing_vars = []
        
        for var_name, description in self.REQUIRED_VARS.items():
            var_value = getattr(self, var_name, None)
            if not var_value:
                missing_vars.append(f"{var_name} ({description})")
        
        if missing_vars:
            error_msg = (
                "❌ Configuration validation failed! Missing required environment variables:\n"
                + "\n".join(f"  - {var}" for var in missing_vars)
                + "\n\n"
                "Please set these variables in your .env file or environment.\n"
                "See .env.example for reference values."
            )
            print(error_msg, file=sys.stderr)
            sys.exit(1)
    
    def validate_recommended_vars(self) -> None:
        """Validate that recommended environment variables are present."""
        missing_vars = []
        
        for var_name, description in self.RECOMMENDED_VARS.items():
            var_value = getattr(self, var_name, None)
            if not var_value:
                missing_vars.append(f"{var_name} ({description})")
        
        if missing_vars:
            print(
                "⚠️  Warning: The following recommended environment variables are missing:\n"
                + "\n".join(f"  - {var}" for var in missing_vars)
                + "\n\n"
                "These variables are recommended for full functionality.",
                file=sys.stderr
            )
    
    def validate_all(self) -> None:
        """Run all configuration validations."""
        print("🔍 Validating configuration...")
        self.validate_required_vars()
        self.validate_recommended_vars()
        print("✅ Configuration validation passed!")
    
# Create a singleton instance
_config_validator = None


def get_config_validator() -> ConfigValidator:
    """Get or create the config validator instance."""
    global _config_validator
    if _config_validator is None:
        _config_validator = ConfigValidator()
    return _config_validator


def validate_config() -> None:
    """Validate the current configuration."""
    validator = get_config_validator()
    validator.validate_all()
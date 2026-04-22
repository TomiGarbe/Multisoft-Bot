from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
from typing import Optional
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Application configuration using Pydantic V2 Settings.
    
    Environment Variables Priority:
    1. Explicitly set values in code
    2. .env file values
    3. Default values defined below
    
    Supports multiple environments: development, production, testing
    """
    
    # ========== ENVIRONMENT ==========
    ENV: str = Field(default="development", description="Environment: development, production, testing")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # ========== APPLICATION INFO ==========
    PROJECT_NAME: str = "Multisoft Bot"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "SaaS platform for conversational bots"
    API_V1_STR: str = "/api/v1"
    
    # ========== DATABASE CONFIGURATION ==========
    # Option 1: Use individual components
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "multisoft_bot"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    
    # Option 2: Direct DATABASE_URL (overrides individual components)
    DATABASE_URL: Optional[str] = None
    
    # SQLAlchemy settings
    SQLALCHEMY_ECHO: bool = False  # Log SQL queries
    SQLALCHEMY_POOL_SIZE: int = 20
    SQLALCHEMY_POOL_RECYCLE: int = 3600  # Recycle connections after 1 hour
    SQLALCHEMY_POOL_PRE_PING: bool = True  # Verify connection before using
    
    # ========== SECURITY ==========
    SECRET_KEY: str = Field(
        ...,  # Required, no default
        description="Secret key for JWT and session encryption (min 32 chars)"
    )
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # ========== CORS SETTINGS ==========
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def allowed_hosts_list(self) -> list[str]:
        """Parse ALLOWED_HOSTS string to list"""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]
    
    # ========== MODEL CONFIGURATION ==========
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    
    # ========== VALIDATORS ==========
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def build_database_url(cls, v: Optional[str], values) -> str:
        """
        Build DATABASE_URL from individual components if not explicitly set.
        
        If DATABASE_URL is provided in .env or directly, use it.
        Otherwise, construct from DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
        """
        if v:
            # DATABASE_URL was explicitly provided
            return v
        
        # Build from individual components
        data = values.data
        db_host = data.get("DB_HOST", "localhost")
        db_port = data.get("DB_PORT", 5432)
        db_name = data.get("DB_NAME", "multisoft_bot")
        db_user = data.get("DB_USER", "postgres")
        db_password = data.get("DB_PASSWORD", "postgres")
        
        # Use postgresql+psycopg for psycopg3 (modern driver)
        return f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v) -> bool:
        """Parse DEBUG as boolean from string"""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return False
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure SECRET_KEY is at least 32 characters in production"""
        if len(v) < 32:
            import warnings
            warnings.warn(
                "⚠️  WARNING: SECRET_KEY is less than 32 characters. "
                "This is insecure for production!",
                stacklevel=2
            )
        return v
    
    # ========== PROPERTIES FOR CONVENIENCE ==========
    @property
    def is_development(self) -> bool:
        return self.ENV.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.ENV.lower() == "testing"


# ========== SINGLETON INSTANCE ==========
# This is loaded once when the module is imported
settings = Settings()

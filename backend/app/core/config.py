from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "Multisoft Bot"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "SaaS platform for conversational bots"
    API_V1_STR: str = "/api/v1"

    # Database - Separate variables for flexibility
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "multisoft_bot"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DATABASE_URL: str | None = None  # Can be set directly if needed

    # Security
    SECRET_KEY: str
    JWT_EXPIRE_MINUTES: int = 1440

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def build_database_url(cls, v: str | None, values) -> str:
        """Build DATABASE_URL from individual components if not explicitly set."""
        if v:
            # If DATABASE_URL is explicitly set, use it
            return v
        
        # Build from components
        data = values.data
        host = data.get("DB_HOST", "localhost")
        port = data.get("DB_PORT", 5432)
        name = data.get("DB_NAME", "multisoft_bot")
        user = data.get("DB_USER", "postgres")
        password = data.get("DB_PASSWORD", "postgres")
        
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


settings = Settings()
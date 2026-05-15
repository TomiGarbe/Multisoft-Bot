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
    SECURITY_BOOTSTRAP_ENABLED: bool = True
    INITIAL_BACKDOOR_NAME: str = "Initial Backdoor"
    INITIAL_BACKDOOR_EMAIL: Optional[str] = None
    INITIAL_BACKDOOR_PASSWORD: Optional[str] = None
    
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

    @property
    def attachment_allowed_mime_types_list(self) -> list[str]:
        return [mime.strip().lower() for mime in self.ATTACHMENT_ALLOWED_MIME_TYPES.split(",") if mime.strip()]

    @property
    def ai_vision_allowed_mime_types_list(self) -> list[str]:
        return [mime.strip().lower() for mime in self.AI_VISION_ALLOWED_MIME_TYPES.split(",") if mime.strip()]
    
    # ========== OLLAMA AI CONFIGURATION ==========
    OLLAMA_BASE_URL: str = Field(
        ...,
        description="Base URL for Ollama API (e.g., http://localhost:11434)"
    )
    OLLAMA_MODEL: str = Field(
        default="gpt-oss:20b",
        description="Ollama model to use for AI generation"
    )
    OLLAMA_TOKEN: Optional[str] = Field(
        default=None,
        description="Optional authentication token for Ollama API"
    )
    OLLAMA_TIMEOUT_SECONDS: float = Field(
        default=300.0,
        description="Timeout in seconds for Ollama requests",
    )
    AI_PROVIDER: str = Field(
        default="deepseek",
        description="Default AI provider (ollama, deepseek, mock)",
    )

    # ========== DEEPSEEK AI CONFIGURATION ==========
    DEEPSEEK_BASE_URL: str = Field(
        default="https://api.deepseek.com",
        description="Base URL for DeepSeek API",
    )
    DEEPSEEK_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for DeepSeek API",
    )
    DEEPSEEK_MODEL: str = Field(
        default="deepseek-chat",
        description="DeepSeek model to use for chat generation",
    )
    DEEPSEEK_TIMEOUT_SECONDS: float = Field(
        default=60.0,
        description="Timeout in seconds for DeepSeek requests",
    )
    DEEPSEEK_MAX_RETRIES: int = Field(
        default=2,
        description="Maximum retry attempts for retryable DeepSeek failures",
    )
    DEEPSEEK_INITIAL_BACKOFF_SECONDS: float = Field(
        default=0.5,
        description="Initial backoff for DeepSeek retries",
    )
    DEEPSEEK_MAX_BACKOFF_SECONDS: float = Field(
        default=3.0,
        description="Maximum backoff for DeepSeek retries",
    )
    AI_VISION_MAX_IMAGES_PER_REQUEST: int = Field(
        default=3,
        description="Maximum number of images to include in a single multimodal AI request",
    )
    AI_VISION_MAX_IMAGE_BYTES: int = Field(
        default=3 * 1024 * 1024,
        description="Maximum bytes allowed per image included in multimodal AI requests",
    )
    AI_VISION_ALLOWED_MIME_TYPES: str = Field(
        default="image/jpeg,image/png,image/webp",
        description="Comma-separated list of MIME types allowed for multimodal AI image inputs",
    )
    AI_MAX_PROMPT_CHARS: int = Field(
        default=32000,
        description="Maximum prompt characters for AI text payloads before truncation",
    )
    AI_MAX_MULTIMODAL_PAYLOAD_BYTES: int = Field(
        default=5 * 1024 * 1024,
        description="Maximum approximate JSON payload size for multimodal AI requests",
    )

    # ========== WHATSAPP MULTISOFT ==========
    WHATSAPP_MULTISOFT_WEBHOOK_URL: Optional[str] = Field(
        default=None,
        description="Outgoing webhook URL for Multisoft WhatsApp service",
    )
    WHATSAPP_MULTISOFT_TIMEOUT_SECONDS: float = Field(
        default=15.0,
        description="Timeout in seconds for Multisoft WhatsApp outbound HTTP calls",
    )
    WHATSAPP_ALLOWED_NUMBERS: str = Field(
        default="",
        description="Comma-separated WhatsApp sender numbers allowed for inbound private messages",
    )
    WHATSAPP_ALLOWED_GROUPS: str = Field(
        default="",
        description="Comma-separated WhatsApp group IDs allowed for inbound group messages",
    )
    ATTACHMENT_DOWNLOAD_TIMEOUT_SECONDS: float = Field(
        default=20.0,
        description="Timeout in seconds for attachment downloads",
    )
    ATTACHMENT_DOWNLOAD_MAX_RETRIES: int = Field(
        default=2,
        description="Maximum retry attempts for attachment download failures",
    )
    ATTACHMENT_DOWNLOAD_INITIAL_BACKOFF_SECONDS: float = Field(
        default=0.5,
        description="Initial backoff delay for attachment download retries",
    )
    ATTACHMENT_DOWNLOAD_MAX_BACKOFF_SECONDS: float = Field(
        default=5.0,
        description="Maximum backoff delay for attachment download retries",
    )
    PROVIDER_HTTP_MAX_RETRIES: int = Field(
        default=2,
        description="Maximum retry attempts for outbound provider HTTP calls",
    )
    PROVIDER_HTTP_INITIAL_BACKOFF_SECONDS: float = Field(
        default=0.4,
        description="Initial backoff delay for outbound provider HTTP retries",
    )
    PROVIDER_HTTP_MAX_BACKOFF_SECONDS: float = Field(
        default=3.0,
        description="Maximum backoff delay for outbound provider HTTP retries",
    )
    ATTACHMENT_ALLOWED_MIME_TYPES: str = Field(
        default=(
            "image/jpeg,image/png,image/webp,image/gif,"
            "audio/mpeg,audio/mp4,audio/ogg,audio/wav,audio/webm,"
            "video/mp4,video/webm,video/quicktime,"
            "application/pdf,text/plain,"
            "application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
            "application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        description="Comma-separated list of allowed attachment MIME types",
    )
    ATTACHMENT_MAX_IMAGE_BYTES: int = Field(default=10 * 1024 * 1024, description="Max bytes for images")
    ATTACHMENT_MAX_AUDIO_BYTES: int = Field(default=20 * 1024 * 1024, description="Max bytes for audio")
    ATTACHMENT_MAX_VIDEO_BYTES: int = Field(default=50 * 1024 * 1024, description="Max bytes for video")
    ATTACHMENT_MAX_DOCUMENT_BYTES: int = Field(default=25 * 1024 * 1024, description="Max bytes for documents")
    MEDIA_TRANSCRIPTION_ENABLED: bool = Field(default=True, description="Enable transcription pipeline")
    MEDIA_DOCUMENT_EXTRACTION_ENABLED: bool = Field(default=True, description="Enable document extraction pipeline")
    MEDIA_MAX_AUDIO_DURATION_MS: int = Field(default=20 * 60 * 1000, description="Max audio duration for STT")
    MEDIA_MAX_DOCUMENT_PAGES: int = Field(default=100, description="Max pages for document extraction")
    MEDIA_PROCESSING_MAX_RETRIES: int = Field(default=2, description="Max retries for media AI jobs")
    MEDIA_PROCESSING_INITIAL_BACKOFF_SECONDS: float = Field(default=0.8, description="Initial backoff for media jobs")
    MEDIA_PROCESSING_MAX_BACKOFF_SECONDS: float = Field(default=8.0, description="Max backoff for media jobs")
    MEDIA_STT_ENABLED: bool = Field(default=False, description="Enable STT provider calls")
    MEDIA_STT_BASE_URL: str = Field(default="https://api.openai.com/v1", description="STT API base URL")
    MEDIA_STT_API_KEY: Optional[str] = Field(default=None, description="STT API key")
    MEDIA_STT_MODEL: str = Field(default="whisper-1", description="STT model name")
    MEDIA_STT_TIMEOUT_SECONDS: float = Field(default=60.0, description="Timeout for STT calls")
    WHISPER_MODEL: str = Field(default="small", description="Local faster-whisper model name")
    WHISPER_DEVICE: str = Field(default="cpu", description="Execution device for faster-whisper (cpu/cuda)")
    WHISPER_COMPUTE_TYPE: str = Field(default="int8", description="CTranslate2 compute type for faster-whisper")
    WHISPER_LANGUAGE: Optional[str] = Field(default=None, description="Optional language hint for transcription")
    WHISPER_TRANSCRIPTION_TIMEOUT_SECONDS: float = Field(
        default=180.0,
        description="Timeout in seconds for a single faster-whisper transcription",
    )
    WHISPER_FFMPEG_TIMEOUT_SECONDS: float = Field(
        default=45.0,
        description="Timeout in seconds for ffmpeg audio conversion",
    )

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

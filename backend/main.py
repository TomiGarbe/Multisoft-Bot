from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import logging
import shutil

from app.api.routes import (
    analytics,
    ai,
    api_keys,
    attachments,
    auth,
    bot_actions,
    channel_bot_config_actions,
    channel_config,
    channels,
    conversations,
    messages,
    media_processing,
    permissions,
    realtime,
    roles,
    tenants,
    users,
    webhooks,
)
from app.bootstrap.security import SecurityBootstrapService
from app.core.config import settings
from app.core.datetime_utils import reset_current_tenant_timezone
from app.core.serialization import configure_datetime_encoder
from app.db.session import SessionLocal
from app.services.whisper_transcription_service import WhisperTranscriptionService

logger = logging.getLogger(__name__)


class _UvicornAccessNoiseFilter(logging.Filter):
    """Suppress high-frequency media-processing polling access logs."""

    _BASE_PATH_TOKEN = "/api/v1/media-processing/attachments/"
    _SUFFIXES = ("/status", "/artifacts")

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            return True
        if self._BASE_PATH_TOKEN not in message:
            return True
        if any(suffix in message for suffix in self._SUFFIXES):
            return False
        return True


logging.getLogger("uvicorn.access").addFilter(_UvicornAccessNoiseFilter())

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
)
configure_datetime_encoder()


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request, exc: RequestValidationError):
    logger.warning(
        "[MULTIMEDIA][UPLOAD] validation_error path=%s method=%s errors=%s",
        request.url.path,
        request.method,
        exc.errors(),
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth")
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users")
app.include_router(roles.router, prefix=f"{settings.API_V1_STR}/roles")
app.include_router(permissions.router, prefix=f"{settings.API_V1_STR}/permissions")
app.include_router(tenants.router, prefix=f"{settings.API_V1_STR}/tenants")
app.include_router(channels.router, prefix=f"{settings.API_V1_STR}/channels")
app.include_router(channel_config.router, prefix=f"{settings.API_V1_STR}/channel-config")
app.include_router(channel_bot_config_actions.router, prefix=f"{settings.API_V1_STR}/channel-bot-configs")
app.include_router(webhooks.router, prefix=f"{settings.API_V1_STR}/webhooks")
app.include_router(messages.router, prefix=f"{settings.API_V1_STR}/messages")
app.include_router(attachments.router, prefix=f"{settings.API_V1_STR}/attachments")
app.include_router(media_processing.router, prefix=f"{settings.API_V1_STR}/media-processing")
app.include_router(conversations.router, prefix=f"{settings.API_V1_STR}/conversations")
app.include_router(ai.router, prefix=f"{settings.API_V1_STR}/ai")
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics")
app.include_router(realtime.router, prefix=f"{settings.API_V1_STR}/realtime")
app.include_router(api_keys.router, prefix=f"{settings.API_V1_STR}/api-keys")
app.include_router(bot_actions.router, prefix=f"{settings.API_V1_STR}/bot-actions")


@app.middleware("http")
async def reset_tenant_timezone_context(request, call_next):
    reset_current_tenant_timezone()
    response = await call_next(request)
    return response


@app.on_event("startup")
def bootstrap_security() -> None:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        logger.info("ffmpeg available at %s", ffmpeg_path)
    else:
        logger.warning("ffmpeg missing in PATH")

    whisper_ok, whisper_state, whisper_detail = WhisperTranscriptionService.validate_startup_dependencies()
    if whisper_ok:
        logger.info("[WHISPER] ready")
    else:
        logger.warning("[WHISPER] %s detail=%s", whisper_state, whisper_detail)

    if not settings.SECURITY_BOOTSTRAP_ENABLED:
        logger.info("Security bootstrap is disabled by configuration.")
        return

    db = SessionLocal()
    try:
        result = SecurityBootstrapService(db).run()
        logger.info(
            "Security bootstrap finished: created_permissions=%s created_roles=%s created_backdoor_user=%s",
            result.created_permissions,
            result.created_roles,
            result.created_backdoor_user,
        )
    finally:
        db.close()


@app.get('/health')
async def health_check():
    """Basic health check."""
    return {
        'status': 'healthy',
        'service': settings.PROJECT_NAME,
        'version': settings.VERSION,
    }


@app.get('/health/db')
async def health_check_db():
    """Health check with database connection test."""
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db.close()
            return {
                'status': 'healthy',
                'database': 'connected',
                'host': settings.DB_HOST,
                'port': settings.DB_PORT,
                'database_name': settings.DB_NAME,
            }
        except Exception as e:
            db.close()
            return {
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e),
                'host': settings.DB_HOST,
                'port': settings.DB_PORT,
                'database_name': settings.DB_NAME,
            }, 503
    except Exception as e:
        return {
            'status': 'unhealthy',
            'database': 'error',
            'error': str(e),
        }, 503

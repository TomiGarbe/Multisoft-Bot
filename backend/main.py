from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import logging

from app.api.routes import ai, api_keys, auth, channel_config, channels, conversations, messages, permissions, realtime, roles, tenants, users, webhooks
from app.bootstrap.security import SecurityBootstrapService
from app.core.config import settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
)

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
app.include_router(webhooks.router, prefix=f"{settings.API_V1_STR}/webhooks")
app.include_router(messages.router, prefix=f"{settings.API_V1_STR}/messages")
app.include_router(conversations.router, prefix=f"{settings.API_V1_STR}/conversations")
app.include_router(ai.router, prefix=f"{settings.API_V1_STR}/ai")
app.include_router(realtime.router, prefix=f"{settings.API_V1_STR}/realtime")
app.include_router(api_keys.router, prefix=f"{settings.API_V1_STR}/api-keys")


@app.on_event("startup")
def bootstrap_security() -> None:
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

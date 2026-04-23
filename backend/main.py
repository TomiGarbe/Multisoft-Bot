from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import auth, channels, permissions, roles, tenants, users
from app.core.config import settings
from app.db.session import SessionLocal

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

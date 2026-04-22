from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.core.config import settings
from app.api.v1.api import api_router
from app.modules.auth.routes import router as auth_router
from app.db.session import SessionLocal, engine

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

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get('/health')
async def health_check():
    """Basic health check."""
    return {
        'status': 'healthy',
        'service': settings.PROJECT_NAME,
        'version': settings.VERSION
    }


@app.get('/health/db')
async def health_check_db():
    """Health check with database connection test."""
    try:
        # Try to get a connection from the pool
        db = SessionLocal()
        try:
            # Execute a simple query to verify connection
            db.execute("SELECT 1")
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
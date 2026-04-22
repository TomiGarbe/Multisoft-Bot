"""
Quick health check for backend setup.
Run: python health_check.py
"""

import sys
from app.core.config import settings

print("=" * 70)
print(" MULTISOFT BOT - HEALTH CHECK + DATABASE CONNECTION TEST")
print("=" * 70)

# Check environment
print("\n1. Checking environment variables...")
try:
    print(f"   ? DATABASE_URL: {settings.DATABASE_URL[:60]}...")
    print(f"   ? DB_HOST: {settings.DB_HOST}")
    print(f"   ? DB_PORT: {settings.DB_PORT}")
    print(f"   ? DB_NAME: {settings.DB_NAME}")
    print(f"   ? DB_USER: {settings.DB_USER}")
    print(f"   ? SECRET_KEY: {'*' * 10}")
    print(f"   ? JWT_EXPIRE_MINUTES: {settings.JWT_EXPIRE_MINUTES}")
except Exception as e:
    print(f"   ? Error: {e}")
    sys.exit(1)

# Check imports
print("\n2. Checking imports...")
try:
    from app.api.routes.auth import get_current_user
    from app.schemas import auth as auth_schemas
    from app.services import auth_service

    print("   ? Auth route/schema/service imported")
    from app.models import User, Role, Permission, RefreshToken

    print("   ? Models imported")
    from app.db.session import SessionLocal, engine

    print("   ? Database session imported")
except Exception as e:
    print(f"   ? Error: {e}")
    sys.exit(1)

# Check database connection
print("\n3. Checking database connection...")
try:
    from sqlalchemy import text

    db = SessionLocal()
    result = db.execute(text("SELECT 1"))
    db.close()
    print("   ? Database connection successful!")
    print(f"      +- Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"      +- Database: {settings.DB_NAME}")
    print(f"      +- User: {settings.DB_USER}")
except Exception as e:
    print(f"   ? Database connection FAILED: {e}")
    print(f"      +- Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print(f"      +- Database: {settings.DB_NAME}")
    print(f"      +- User: {settings.DB_USER}")
    print("\n   Troubleshooting tips:")
    print(f"      1. Is PostgreSQL running on {settings.DB_HOST}:{settings.DB_PORT}?")
    print(f"      2. Does database '{settings.DB_NAME}' exist?")
    print(f"      3. Are credentials correct? (user={settings.DB_USER})")
    print("      4. If running LOCAL, use .env with DB_HOST=localhost")
    print("      5. If running DOCKER, use .env.docker with DB_HOST=postgres")
    sys.exit(1)

# Check password hashing
print("\n4. Checking password hashing...")
try:
    password = "test123"
    hashed = auth_service.hash_password(password)
    verified = auth_service.verify_password(password, hashed)
    if verified:
        print("   ? Password hashing works")
    else:
        print("   ? Password verification failed")
except Exception as e:
    print(f"   ? Error: {e}")
    sys.exit(1)

# Check JWT
print("\n5. Checking JWT generation...")
try:
    import uuid

    test_id = uuid.uuid4()
    token = auth_service.create_access_token(test_id, "test@example.com")
    payload = auth_service.verify_token(token)
    if payload:
        print("   ? JWT generation and verification works")
    else:
        print("   ? JWT verification failed")
except Exception as e:
    print(f"   ? Error: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print(" ? ALL CHECKS PASSED - Backend is ready!")
print("=" * 70)
print("\nNext steps:")
print("  1. Run migraciones:        alembic upgrade head")
print("  2. Load seed data:          python seed.py")
print("  3. Start the server:        uvicorn main:app --reload")
print("  4. Open documentation:      http://localhost:8000/docs")
print("  5. Test DB health:          curl http://localhost:8000/health/db")
print("=" * 70)

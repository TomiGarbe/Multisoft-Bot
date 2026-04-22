#!/usr/bin/env python3
"""
Quick test to verify configuration works correctly.
Run: python test_config.py
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

print("\n" + "=" * 70)
print(" DATABASE CONFIGURATION TEST")
print("=" * 70)

print("\n📋 Configuration Variables:")
print(f"   DB_HOST:      {settings.DB_HOST}")
print(f"   DB_PORT:      {settings.DB_PORT}")
print(f"   DB_NAME:      {settings.DB_NAME}")
print(f"   DB_USER:      {settings.DB_USER}")
print(f"   DB_PASSWORD:  {'*' * len(settings.DB_PASSWORD)}")
print(f"\n🔗 Generated DATABASE_URL:")
print(f"   {settings.DATABASE_URL}")

# Validate format
if "postgresql+psycopg://" in settings.DATABASE_URL:
    print("\n✅ Format is correct: postgresql+psycopg://")
else:
    print("\n❌ Format is INCORRECT!")
    sys.exit(1)

# Check if components are in the URL
if settings.DB_USER in settings.DATABASE_URL:
    print(f"✅ User '{settings.DB_USER}' in URL")
else:
    print(f"❌ User NOT in URL")

if settings.DB_HOST in settings.DATABASE_URL:
    print(f"✅ Host '{settings.DB_HOST}' in URL")
else:
    print(f"❌ Host NOT in URL")

if str(settings.DB_PORT) in settings.DATABASE_URL:
    print(f"✅ Port '{settings.DB_PORT}' in URL")
else:
    print(f"❌ Port NOT in URL")

if settings.DB_NAME in settings.DATABASE_URL:
    print(f"✅ Database name '{settings.DB_NAME}' in URL")
else:
    print(f"❌ Database name NOT in URL")

print("\n" + "=" * 70)
print(" ✓ Configuration is correctly formatted")
print("=" * 70)
print("\n💡 To test actual database connection:")
print("   python health_check.py")
print("\n")

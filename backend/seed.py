"""
Seed script to initialize database with default data.
Uses centralized configuration from app.core.config

Run locally: python seed.py
Run in Docker: docker exec multisoft_bot_backend python seed.py
"""

import sys
from sqlalchemy import select, create_engine

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.base import Base
from app.models import User, Permission, Role
from app.services.auth_service import hash_password


def seed_database():
    """Initialize database with default data."""
    
    print("\n" + "=" * 70)
    print(" DATABASE SEEDING")
    print("=" * 70)
    print(f"📍 Using DATABASE_URL: {settings.DATABASE_URL}")
    print(f"📍 Environment: {settings.ENV}")
    
    try:
        # Create engine and tables using the same DATABASE_URL as the app
        engine = create_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
        )
        
        # Create all tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("\n✓ Tables created/verified")
        
        # Get database session
        db = SessionLocal()
        
        try:
            # ========== CREATE ADMIN USER ==========
            stmt = select(User).where(User.email == "admin@test.com")
            existing_admin = db.execute(stmt).scalar_one_or_none()
            
            if not existing_admin:
                admin = User(
                    name="Admin User",
                    email="admin@test.com",
                    password_hash=hash_password("123456"),
                    is_active=True,
                    is_backdoor=True,
                )
                db.add(admin)
                db.flush()
                print(f"✓ Created admin user: admin@test.com (password: 123456)")
            else:
                existing_admin.is_backdoor = True
                existing_admin.is_active = True
                print(f"⊘ Admin user already exists")
            
            # ========== CREATE DEFAULT PERMISSIONS ==========
            default_permissions = [
                ("USER_CREATE", "Create User", "Ability to create new users"),
                ("USER_READ", "Read User", "Ability to view user details"),
                ("USER_UPDATE", "Update User", "Ability to update user information"),
                ("USER_DELETE", "Delete User", "Ability to delete users"),
                ("ROLE_CREATE", "Create Role", "Ability to create new roles"),
                ("ROLE_READ", "Read Role", "Ability to view role details"),
                ("ROLE_UPDATE", "Update Role", "Ability to update roles"),
                ("ROLE_DELETE", "Delete Role", "Ability to delete roles"),
                ("PERMISSION_CREATE", "Create Permission", "Ability to create new permissions"),
                ("PERMISSION_READ", "Read Permission", "Ability to view permissions"),
                ("PERMISSION_UPDATE", "Update Permission", "Ability to update permissions"),
                ("PERMISSION_DELETE", "Delete Permission", "Ability to delete permissions"),
                ("tenants.create", "Create Tenant", "Ability to create new tenants"),
                ("tenants.read", "Read Tenant", "Ability to view tenant details"),
                ("tenants.update", "Update Tenant", "Ability to update tenants"),
                ("tenants.delete", "Delete Tenant", "Ability to delete tenants"),
            ]
            
            created_count = 0
            for code, name, description in default_permissions:
                stmt = select(Permission).where(Permission.code == code)
                existing = db.execute(stmt).scalar_one_or_none()
                if not existing:
                    permission = Permission(
                        code=code,
                        name=name,
                        description=description
                    )
                    db.add(permission)
                    created_count += 1
            
            if created_count > 0:
                print(f"✓ Created {created_count} permissions")
            else:
                print(f"⊘ All permissions already exist")
            
            # ========== CREATE DEFAULT ADMIN ROLE ==========
            stmt = select(Role).where(Role.name == "Admin")
            existing_admin_role = db.execute(stmt).scalar_one_or_none()
            
            if not existing_admin_role:
                admin_role = Role(
                    name="Admin",
                    description="System administrator role",
                    is_system=True
                )
                db.add(admin_role)
                db.flush()
                print(f"✓ Created admin role")
            else:
                print(f"⊘ Admin role already exists")
            
            # Commit all changes
            db.commit()
            print("\n" + "=" * 70)
            print("✓ Database seeded successfully!")
            print("=" * 70 + "\n")
            return True
            
        except Exception as e:
            db.rollback()
            print(f"\n✗ Error during seeding: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()
    
    except Exception as e:
        print(f"\n✗ Error connecting to database: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = seed_database()
    sys.exit(0 if success else 1)



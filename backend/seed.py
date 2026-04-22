"""
Seed script to initialize database with default data.
Run: python seed.py
"""

from app.db.session import SessionLocal
from app.db.base import Base
from app.models import User, Permission, Role
from app.modules.auth.service import hash_password
from sqlalchemy import create_engine
from app.core.config import settings

def seed_database():
    """Initialize database with default data."""
    
    # Create tables
    database_url = settings.DATABASE_URL.replace("postgresql+psycopg://", "postgresql+psycopg2://")
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        from sqlalchemy import select
        stmt = select(User).where(User.email == "admin@test.com")
        existing_admin = db.execute(stmt).scalar_one_or_none()
        
        if not existing_admin:
            # Create admin user
            admin = User(
                name="Admin User",
                email="admin@test.com",
                password_hash=hash_password("123456"),
                is_active=True
            )
            db.add(admin)
            db.flush()
            print(f"✓ Created admin user: admin@test.com")
        
        # Create default permissions
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
        ]
        
        from sqlalchemy import select
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
                print(f"✓ Created permission: {code}")
        
        # Create default admin role
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
        
        db.commit()
        print("\n✓ Database seeded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

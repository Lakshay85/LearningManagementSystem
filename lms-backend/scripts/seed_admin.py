import os
import sys
import argparse
import asyncio
from uuid import uuid4

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.database_init import init_database
from app.models.models import User, Admin
from app.models.enums import UserRole, UserStatus, Permission
from app.auth.service import AuthService

async def seed_admin(email: str, password: str, first_name: str, last_name: str, department: str = "Administration"):
    email_clean = email.strip().lower()
    all_permissions = [p.value for p in Permission]

    # Initialize tables and migrations first
    await init_database()

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.email == email_clean))
        user = res.scalar_one_or_none()

        if user:
            print(f"ℹ️ User with email '{email_clean}' already exists (ID: {user.id}).")
            user.role = "admin"
            user.isActive = True
            user.status = UserStatus.ACTIVE

            admin_res = await db.execute(select(Admin).where(Admin.userId == user.id))
            admin = admin_res.scalar_one_or_none()

            if not admin:
                admin = Admin(
                    userId=user.id,
                    adminLevel="super",
                    permissions=all_permissions,
                    department=department
                )
                db.add(admin)
                print("✅ Created new Super Admin record for existing user.")
            else:
                admin.adminLevel = "super"
                admin.permissions = all_permissions
                admin.department = department
                print("✅ Updated existing user to Super Admin with all permissions.")

            await db.commit()
            print(f"🎉 Admin account ready: {email_clean}")
            return

        # Create new admin user
        hashed_password = AuthService.hash_password(password)
        new_user = User(
            email=email_clean,
            password=hashed_password,
            firstName=first_name,
            lastName=last_name,
            role="admin",
            isActive=True,
            status=UserStatus.ACTIVE
        )
        db.add(new_user)
        await db.flush()

        admin_record = Admin(
            userId=new_user.id,
            adminLevel="super",
            permissions=all_permissions,
            department=department
        )
        db.add(admin_record)
        await db.commit()

        print(f"✅ Created Super Admin account successfully!")
        print(f"   Email: {email_clean}")
        print(f"   Name: {first_name} {last_name}")
        print(f"   Role: admin (super)")
        print(f"   Permissions: {len(all_permissions)} granted")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed initial Super Admin user for LMS")
    parser.add_argument("--email", default="admin@lms.com", help="Admin email address")
    parser.add_argument("--password", default="Admin123!", help="Admin password")
    parser.add_argument("--firstName", default="Super", help="First name")
    parser.add_argument("--lastName", default="Admin", help="Last name")
    parser.add_argument("--department", default="Administration", help="Department")

    args = parser.parse_args()
    asyncio.run(seed_admin(
        email=args.email,
        password=args.password,
        first_name=args.firstName,
        last_name=args.lastName,
        department=args.department
    ))

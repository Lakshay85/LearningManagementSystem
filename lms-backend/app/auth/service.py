import os
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.config import settings
from app.models.models import User, Student, Teacher, NotificationPreference
from app.models.enums import UserRole, UserStatus
from app.auth.schemas import SignupSchema, FacultySignupSchema, LoginSchema, UpdatePasswordSchema, UpdateProfileSchema

# Simple HTTP exception class to raise inside services or caught in endpoints
from fastapi import HTTPException, status

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        # Replicates Node.js scrypt behavior
        salt = os.urandom(16)
        # N=16384, r=8, p=1, dklen=64 are default Node.js crypto.scrypt options
        derived_key = hashlib.scrypt(
            password.encode('utf-8'),
            salt=salt,
            n=16384,
            r=8,
            p=1,
            dklen=64
        )
        return f"{salt.hex()}:{derived_key.hex()}"

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        try:
            salt_hex, key_hex = hashed.split(":")
            salt = bytes.fromhex(salt_hex)
            derived_key = hashlib.scrypt(
                password.encode('utf-8'),
                salt=salt,
                n=16384,
                r=8,
                p=1,
                dklen=64
            )
            return derived_key.hex() == key_hex
        except Exception:
            return False

    @classmethod
    async def generate_tokens(cls, user: User) -> Tuple[str, str]:
        # Encode UUID as string for JWT
        user_id_str = str(user.id)
        
        access_payload = {
            "sub": user_id_str,
            "email": user.email,
            "role": user.role,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
        }
        
        refresh_payload = {
            "sub": user_id_str,
            "email": user.email,
            "role": user.role,
            "exp": datetime.now(timezone.utc) + timedelta(days=7)
        }

        access_token = jwt.encode(
            access_payload,
            settings.JWT_ACCESS_SECRET,
            algorithm="HS256"
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            settings.JWT_REFRESH_SECRET,
            algorithm="HS256"
        )
        
        return access_token, refresh_token

    async def signup(self, db: AsyncSession, signup_dto: SignupSchema) -> Dict[str, Any]:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == signup_dto.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )

        hashed_password = self.hash_password(signup_dto.password)

        # Create user
        user = User(
            email=signup_dto.email,
            password=hashed_password,
            firstName=signup_dto.firstName,
            lastName=signup_dto.lastName,
            role=UserRole.STUDENT
        )
        db.add(user)
        await db.flush()  # To populate user.id

        # Create student record
        student = Student(
            userId=user.id
        )
        db.add(student)

        # Create default notification preferences
        pref = NotificationPreference(
            userId=user.id
        )
        db.add(pref)

        # Generate tokens
        access_token, refresh_token = await self.generate_tokens(user)
        user.refreshToken = refresh_token

        await db.commit()
        await db.refresh(user)

        return {
            "message": "Student registered successfully",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "firstName": user.firstName,
                "lastName": user.lastName,
                "role": user.role,
            },
            "accessToken": access_token,
            "refreshToken": refresh_token,
        }

    async def faculty_signup(self, db: AsyncSession, signup_dto: FacultySignupSchema) -> Dict[str, Any]:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == signup_dto.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )

        hashed_password = self.hash_password(signup_dto.password)

        # Create user with TEACHER role
        user = User(
            email=signup_dto.email,
            password=hashed_password,
            firstName=signup_dto.firstName,
            lastName=signup_dto.lastName,
            role=UserRole.FACULTY
        )
        db.add(user)
        await db.flush()

        # Create teacher record
        teacher = Teacher(
            userId=user.id,
            department=signup_dto.department,
            specialization=signup_dto.specialization,
            qualification=signup_dto.qualification
        )
        db.add(teacher)

        # Create default notification preferences
        pref = NotificationPreference(
            userId=user.id
        )
        db.add(pref)

        # Generate tokens
        access_token, refresh_token = await self.generate_tokens(user)
        user.refreshToken = refresh_token

        await db.commit()
        await db.refresh(user)

        return {
            "message": "Faculty registered successfully",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "firstName": user.firstName,
                "lastName": user.lastName,
                "role": user.role,
            },
            "accessToken": access_token,
            "refreshToken": refresh_token,
        }

    async def login(self, db: AsyncSession, login_dto: LoginSchema) -> Dict[str, Any]:
        result = await db.execute(select(User).where(User.email == login_dto.email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        if not user.isActive:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )

        if not self.verify_password(login_dto.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Update last login
        user.lastLogin = datetime.now()
        
        # Generate tokens
        access_token, refresh_token = await self.generate_tokens(user)
        user.refreshToken = refresh_token
        
        await db.commit()
        await db.refresh(user)

        return {
            "message": "Login successful",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "firstName": user.firstName,
                "lastName": user.lastName,
                "role": user.role,
            },
            "accessToken": access_token,
            "refreshToken": refresh_token,
        }

    async def refresh_tokens(self, db: AsyncSession, user_id: str, refresh_token: str) -> Dict[str, str]:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access denied"
            )

        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()

        if not user or not user.refreshToken:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access denied"
            )

        if user.refreshToken != refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access denied"
            )

        access_token, new_refresh_token = await self.generate_tokens(user)
        user.refreshToken = new_refresh_token
        
        await db.commit()

        return {
            "accessToken": access_token,
            "refreshToken": new_refresh_token,
        }

    async def logout(self, db: AsyncSession, user_id: str) -> Dict[str, str]:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        user = await db.get(User, user_uuid)
        if user:
            user.refreshToken = None
            await db.commit()

        return {"message": "Logout successful"}

    async def get_current_user(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        user = await db.get(User, user_uuid)
        if not user or not user.isActive:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        if not user.refreshToken:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired"
            )

        return {
            "id": str(user.id),
            "email": user.email,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "role": user.role,
            "profilePictureUrl": user.profilePicture,
        }

    async def update_password(self, db: AsyncSession, user_id: str, dto: UpdatePasswordSchema) -> Dict[str, str]:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        user = await db.get(User, user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if not self.verify_password(dto.currentPassword, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        user.password = self.hash_password(dto.newPassword)
        await db.commit()

        return {"message": "Password updated successfully"}

    async def delete_account(self, db: AsyncSession, user_id: str) -> Dict[str, str]:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        user = await db.get(User, user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        user.isActive = False
        await db.commit()

        return {"message": "Account deleted successfully"}

    async def update_profile(self, db: AsyncSession, user_id: str, dto: UpdateProfileSchema) -> Dict[str, Any]:
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        user = await db.get(User, user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        user.firstName = dto.firstName
        user.lastName = dto.lastName
        await db.commit()

        return {
            "message": "Profile updated successfully",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "firstName": user.firstName,
                "lastName": user.lastName,
                "role": user.role,
            }
        }

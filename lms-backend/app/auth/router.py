from fastapi import APIRouter, Depends, Response, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.auth.schemas import (
    SignupSchema, FacultySignupSchema, LoginSchema,
    UpdatePasswordSchema, UpdateProfileSchema
)
from app.auth.service import AuthService
from app.auth.dependencies import get_current_user, get_refresh_token_user

router = APIRouter(prefix="/auth", tags=["Auth"])
service = AuthService()

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    is_prod = settings.NODE_ENV == "production"
    
    response.set_cookie(
        key="accessToken",
        value=access_token,
        httponly=True,
        secure=is_prod,
        samesite="strict",
        max_age=30 * 60  # 30 minutes
    )
    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=is_prod,
        samesite="strict",
        max_age=7 * 24 * 60 * 60  # 7 days
    )

def clear_auth_cookies(response: Response):
    response.delete_cookie(key="accessToken")
    response.delete_cookie(key="refreshToken")


@router.post("/student/signup", status_code=status.HTTP_201_CREATED)
async def student_signup(response: Response, dto: SignupSchema, db: AsyncSession = Depends(get_db)):
    result = await service.signup(db, dto)
    set_auth_cookies(response, result["accessToken"], result["refreshToken"])
    return {
        "message": result["message"],
        "user": result["user"]
    }


@router.post("/faculty/signup", status_code=status.HTTP_201_CREATED)
async def faculty_signup(response: Response, dto: FacultySignupSchema, db: AsyncSession = Depends(get_db)):
    result = await service.faculty_signup(db, dto)
    set_auth_cookies(response, result["accessToken"], result["refreshToken"])
    return {
        "message": result["message"],
        "user": result["user"]
    }


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(response: Response, dto: LoginSchema, db: AsyncSession = Depends(get_db)):
    result = await service.login(db, dto)
    set_auth_cookies(response, result["accessToken"], result["refreshToken"])
    return {
        "message": result["message"],
        "user": result["user"]
    }


# Aliases for backward compatibility
@router.post("/student/login", status_code=status.HTTP_200_OK)
async def student_login(response: Response, dto: LoginSchema, db: AsyncSession = Depends(get_db)):
    return await login(response, dto, db)


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(response: Response, current_refresh_user: dict = Depends(get_refresh_token_user), db: AsyncSession = Depends(get_db)):
    tokens = await service.refresh_tokens(
        db, 
        current_refresh_user["userId"], 
        current_refresh_user["refreshToken"]
    )
    set_auth_cookies(response, tokens["accessToken"], tokens["refreshToken"])
    return {
        "message": "Tokens refreshed successfully"
    }


@router.post("/student/refresh", status_code=status.HTTP_200_OK)
async def student_refresh(response: Response, current_refresh_user: dict = Depends(get_refresh_token_user), db: AsyncSession = Depends(get_db)):
    return await refresh(response, current_refresh_user, db)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await service.logout(db, current_user["userId"])
    clear_auth_cookies(response)
    return result


@router.post("/student/logout", status_code=status.HTTP_200_OK)
async def student_logout(response: Response, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await logout(response, current_user, db)


@router.put("/update-password", status_code=status.HTTP_200_OK)
async def update_password(dto: UpdatePasswordSchema, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await service.update_password(db, current_user["userId"], dto)


@router.delete("/delete-account", status_code=status.HTTP_200_OK)
async def delete_account(response: Response, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await service.delete_account(db, current_user["userId"])
    clear_auth_cookies(response)
    return result


@router.put("/update-profile", status_code=status.HTTP_200_OK)
async def update_profile(dto: UpdateProfileSchema, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await service.update_profile(db, current_user["userId"], dto)


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await service.get_current_user(db, current_user["userId"])

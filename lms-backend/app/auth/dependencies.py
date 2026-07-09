from typing import List, Optional
from fastapi import Request, Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.models import User

# Extractor functions
def extract_access_token(request: Request) -> Optional[str]:
    # Try header first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    
    # Try cookies next
    return request.cookies.get("accessToken")

def extract_refresh_token(request: Request, body_data: Optional[dict] = None) -> Optional[str]:
    # Try body parameter first
    if body_data and "refreshToken" in body_data:
        return body_data["refreshToken"]
    
    # Try cookies next
    return request.cookies.get("refreshToken")

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> dict:
    token = extract_access_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_ACCESS_SECRET,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        
        print(f"DEBUG JWT: email={email}, sub={user_id}, role={role}")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
            
        return {"userId": user_id, "email": email, "role": role}
    except JWTError as e:
        print(f"DEBUG JWT ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

async def get_current_user_optional(request: Request) -> Optional[dict]:
    token = extract_access_token(request)
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.JWT_ACCESS_SECRET,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        
        if user_id:
            return {"userId": user_id, "email": email, "role": role}
    except JWTError:
        pass
    return None

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        print(f"DEBUG ROLECHECKER: user_role={current_user.get('role')}, allowed={self.allowed_roles}")
        if current_user["role"] not in self.allowed_roles:
            roles_str = ", ".join(self.allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: This resource requires one of the following roles: {roles_str}"
            )
        return current_user

require_faculty = RoleChecker(["faculty", "teacher"])
require_student = RoleChecker(["student"])

async def get_refresh_token_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> dict:
    # We must read body if it's sent. Because FastAPI body can only be read once,
    # we need to be careful. However, let's extract it from json body if present.
    body_token = None
    try:
        body = await request.json()
        body_token = body.get("refreshToken")
    except Exception:
        pass

    token = body_token or request.cookies.get("refreshToken")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access denied"
        )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_REFRESH_SECRET,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access denied"
            )
            
        return {"userId": user_id, "email": email, "role": role, "refreshToken": token}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access denied"
        )

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UpdateUserStatusSchema(BaseModel):
    isActive: bool

class UpdateUserRoleSchema(BaseModel):
    role: str  # 'student', 'faculty', 'admin'

class SetLLMLimitSchema(BaseModel):
    llmDailyLimit: Optional[int] = None   # None or 0 = unlimited
    llmMonthlyLimit: Optional[int] = None

class CreateUserSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    firstName: str
    lastName: str
    role: str = "student"  # 'student', 'faculty', 'admin'
    phoneNumber: Optional[str] = None
    department: Optional[str] = None

class ResetPasswordSchema(BaseModel):
    newPassword: str = Field(..., min_length=6)

class UpdateSystemSettingSchema(BaseModel):
    value: Any
    description: Optional[str] = None

class AdminPermissionsSchema(BaseModel):
    permissions: List[str]  # list of Permission enum values

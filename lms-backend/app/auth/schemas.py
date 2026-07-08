from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class SignupSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    firstName: str
    lastName: str

class FacultySignupSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    firstName: str
    lastName: str
    department: Optional[str] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenSchema(BaseModel):
    refreshToken: Optional[str] = None

class UpdatePasswordSchema(BaseModel):
    currentPassword: str
    newPassword: str = Field(..., min_length=6)

class UpdateProfileSchema(BaseModel):
    firstName: str
    lastName: str

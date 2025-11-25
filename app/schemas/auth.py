from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from app.models.contract import UserRole
from app.core.constants import AuthConstants, ErrorMessages


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=AuthConstants.MIN_PASSWORD_LENGTH,
        max_length=AuthConstants.MAX_PASSWORD_LENGTH
    )


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=AuthConstants.MIN_PASSWORD_LENGTH,
        max_length=AuthConstants.MAX_PASSWORD_LENGTH
    )
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    department: str
    position: str = Field(..., min_length=1, max_length=100)
    role: Optional[str] = Field(AuthConstants.DEFAULT_ROLE)

    @validator('password')
    def validate_password_length(cls, v):
        max_len = AuthConstants.MAX_PASSWORD_LENGTH
        if len(v.encode('utf-8')) > max_len:
            raise ValueError(f'Password cannot be longer than {max_len} bytes')
        return v
    
    @validator('role')
    def validate_role(cls, v):
        if v is None:
            return AuthConstants.DEFAULT_ROLE
        
        if v in AuthConstants.VALID_ROLES:
            return v
        
        if v in AuthConstants.ROLE_NAME_TO_VALUE:
            return AuthConstants.ROLE_NAME_TO_VALUE[v]
        
        raise ValueError(ErrorMessages.INVALID_ROLE)


class UserWithRole(BaseModel):
    id: int
    user_id: str
    email: EmailStr
    first_name: str
    last_name: str
    department: str
    position: str
    role: Optional[UserRole]
    is_active: bool

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str = Field(
        ...,
        min_length=AuthConstants.MIN_PASSWORD_LENGTH,
        max_length=AuthConstants.MAX_PASSWORD_LENGTH
    )
    new_password: str = Field(
        ...,
        min_length=AuthConstants.MIN_PASSWORD_LENGTH,
        max_length=AuthConstants.MAX_PASSWORD_LENGTH
    )

    @validator('new_password')
    def validate_password_length(cls, v):
        max_len = AuthConstants.MAX_PASSWORD_LENGTH
        if len(v.encode('utf-8')) > max_len:
            raise ValueError(f'Password cannot be longer than {max_len} bytes')
        return v


class PasswordReset(BaseModel):
    email: EmailStr
    new_password: str = Field(
        ...,
        min_length=AuthConstants.MIN_PASSWORD_LENGTH,
        max_length=AuthConstants.MAX_PASSWORD_LENGTH
    )

    @validator('new_password')
    def validate_password_length(cls, v):
        max_len = AuthConstants.MAX_PASSWORD_LENGTH
        if len(v.encode('utf-8')) > max_len:
            raise ValueError(f'Password cannot be longer than {max_len} bytes')
        return v
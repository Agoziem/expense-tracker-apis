import uuid
from typing import List, Optional, Union
from enum import Enum
from pydantic import UUID4, BaseModel, ConfigDict, Field, EmailStr, field_serializer, HttpUrl
import uuid
from datetime import datetime

from app.api.v1.auth.models import Role



class UserCreateModel(BaseModel):
    """
    User registration model
    """
    first_name: str = Field(max_length=25)
    last_name: str = Field(max_length=25)
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)

    model_config = {
        "json_schema_extra": {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "johndoe123@co.com",
                "password": "testpass123",
            }
        }
    }


class UserResponseModel(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: Optional[str] = None
    email: EmailStr  # Ensures email validation
    phone: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[str] = None
    role: Role = Role.USER

    @field_serializer("id")
    def serialize_uuid(self, value: uuid.UUID) -> str:
        return str(value)
    
    class Config:
        from_attributes = True  # Enables ORM compatibility for SQLAlchemy integration


class UserModel(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: Optional[str] = None
    email: EmailStr  # Ensures email validation
    phone: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    password_hash: Optional[str] = Field(exclude=True)
    avatar: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[str] = None
    role: Role = Role.USER
    is_verified: bool = False
    two_factor_enabled: Optional[bool] = False
    is_oauth: bool = False
    created_at: datetime

    @field_serializer("id")
    def serialize_uuid(self, value: uuid.UUID) -> str:
        return str(value)
    
    @field_serializer("created_at")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()

    class Config:
        from_attributes = True  # Enables ORM compatibility for SQLAlchemy integration


class UserUpdateModel(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None  # Make email optional
    phone: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[str] = None
    profile_completed: Optional[bool] = False

    class Config:
        from_attributes = True


class UserLoginModel(BaseModel):
    email: str = Field(max_length=40)
    password: str = Field(min_length=6)


class EmailModel(BaseModel):
    addresses: List[EmailStr]

class BulkEmailData(BaseModel):
    subject: str
    html_content: str


class TokenRequestModel(BaseModel):
    email: str



class PasswordResetConfirmModel(BaseModel):
    new_password: str
    confirm_new_password: str

class PasswordResetModel(BaseModel):
    new_password: str
    confirm_new_password: str
    old_password: str

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "new_password": "newpassword123",
                "confirm_new_password": "newpassword123",
                "old_password": "oldpassword123"
            }
        }

class ChangeRoleModel(BaseModel):
    user_id: UUID4
    new_role: Role

    @field_serializer("user_id")
    def serialize_uuid(self, value: UUID4) -> str:
        return str(value)
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "new_role": "admin"
            }
        }

class ActivityTypeEnum(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    # Add any other types from your ActivityType enum if needed

class ActivityBase(BaseModel):
    description: str
    activity_type: ActivityTypeEnum = ActivityTypeEnum.CREATE
    user_id: UUID4


class ActivityCreate(ActivityBase):
    pass


class ActivityResponse(ActivityBase):
    id: UUID4
    created_at: datetime

    @field_serializer("id", "user_id", mode="plain")
    def serialize_uuids(self, value):
        return str(value)

    @field_serializer("created_at", mode="plain")
    def serialize_datetime(self, value: datetime):
        return value.isoformat()

    class Config:
        from_attributes = True


# ---------------------------------------------------
# response schemas
# ---------------------------------------------------
class UserInfo(BaseModel):
    id: uuid.UUID
    email: EmailStr
    profile_completed: bool

    @field_serializer("id")
    def serialize_uuid(self, value: uuid.UUID) -> str:
        return str(value)
    
    model_config = ConfigDict(from_attributes=True)

class BaseResponse(BaseModel):
    message: str

class VerificationResponse(BaseResponse):
    verification_needed: bool

class TwoFactorResponse(BaseResponse):
    two_factor_required: bool
    user: dict[str, str]

class LoginSuccessResponse(BaseResponse):
    access_token: str
    refresh_token: str
    user: UserInfo

class TokenResponse(BaseModel):
    access_token: str

class CreateUserResponse(BaseResponse):
    user: UserModel

class LogoutResponse(BaseResponse):
    pass

class PasswordResetResponse(BaseResponse):
    pass

class UserUpdateResponse(BaseResponse):
    user: UserUpdateModel

class UserRoleChangeResponse(BaseResponse):
    user: UserUpdateModel

# Union type for login responses
LoginResponse = Union[VerificationResponse, TwoFactorResponse, LoginSuccessResponse]
# schemas for auth, users, orgs, and memberships

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# registration request - needs email, password, name, and org name
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    organization_name: str = Field(min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()-_=+[]{}|;:',.<>?/`~" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


# what we send back when someone asks for user info
class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserWithMemberships(UserResponse):
    memberships: list["MembershipResponse"] = []


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    password: str | None = Field(None, min_length=8, max_length=128)


# org response schema
class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    subscription_tier: str
    subscription_status: str
    max_users: int
    max_storage_mb: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateOrganizationRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    settings: dict | None = None


# membership schemas
class MembershipResponse(BaseModel):
    id: UUID
    user_id: UUID
    organization_id: UUID
    role: str
    is_active: bool
    joined_at: datetime

    model_config = {"from_attributes": True}


class MemberWithUser(MembershipResponse):
    user: UserResponse


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = Field(pattern="^(admin|lawyer|paralegal)$")
    full_name: str = Field(min_length=1, max_length=255)


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(pattern="^(admin|lawyer|paralegal)$")

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    email_verified: bool


class EmailVerificationConfirmRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

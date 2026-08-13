from enum import StrEnum

from pydantic import BaseModel


class ErrorCode(StrEnum):
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_INVALID_REFRESH_TOKEN = "AUTH_INVALID_REFRESH_TOKEN"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    USER_EMAIL_ALREADY_EXISTS = "USER_EMAIL_ALREADY_EXISTS"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    HTTP_ERROR = "HTTP_ERROR"


class FieldError(BaseModel):
    field: str
    reason: str


class ErrorResponse(BaseModel):
    code: ErrorCode
    message: str
    errors: list[FieldError] | None = None

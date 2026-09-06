from typing import Protocol

from pydantic import BaseModel, EmailStr, Field

from md2blog.modules.identity.domain.commands import (
    ConfirmPasswordResetCommand,
    RequestPasswordResetCommand,
)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)
    new_password: str = Field(min_length=8, max_length=128)


class RequestPasswordResetUseCase(Protocol):
    async def execute(self, command: RequestPasswordResetCommand) -> None: ...


class ConfirmPasswordResetUseCase(Protocol):
    async def execute(self, command: ConfirmPasswordResetCommand) -> None: ...

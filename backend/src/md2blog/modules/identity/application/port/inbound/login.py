from typing import Protocol

from pydantic import BaseModel, EmailStr, Field

from md2blog.modules.identity.application.service.login import LoginResult
from md2blog.modules.identity.domain.commands import LoginCommand


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginUseCase(Protocol):
    async def execute(self, command: LoginCommand) -> LoginResult: ...

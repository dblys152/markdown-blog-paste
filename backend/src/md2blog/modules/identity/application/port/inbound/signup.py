from typing import Annotated, Protocol

from pydantic import BaseModel, EmailStr, Field, StringConstraints

from md2blog.modules.identity.application.service.signup import SignUpResult
from md2blog.modules.identity.domain.commands import SignUpCommand


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=10),
    ]


class SignUpUseCase(Protocol):
    async def execute(self, command: SignUpCommand) -> SignUpResult: ...

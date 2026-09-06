from typing import Protocol

from pydantic import BaseModel, Field

from md2blog.modules.identity.domain.commands import DeleteAccountCommand
from md2blog.modules.identity.domain.user import User


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class DeleteAccountUseCase(Protocol):
    async def execute(self, user: User, command: DeleteAccountCommand) -> None: ...

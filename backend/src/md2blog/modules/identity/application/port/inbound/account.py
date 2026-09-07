from typing import Protocol

from pydantic import BaseModel, Field, model_validator

from md2blog.modules.identity.domain.commands import DeleteAccountCommand
from md2blog.modules.identity.domain.user import User


class DeleteAccountRequest(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=128)
    google_credential: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def require_one_credential(self) -> "DeleteAccountRequest":
        if (self.password is None) == (self.google_credential is None):
            raise ValueError("비밀번호 또는 Google 인증 정보 중 하나가 필요합니다.")
        return self


class DeleteAccountUseCase(Protocol):
    async def execute(self, user: User, command: DeleteAccountCommand) -> None: ...

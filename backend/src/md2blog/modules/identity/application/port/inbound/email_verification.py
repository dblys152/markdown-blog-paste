from typing import Protocol

from md2blog.modules.identity.domain.user import User


class IssueEmailVerificationUseCase(Protocol):
    async def execute(self, user: User) -> None: ...


class ConfirmEmailVerificationUseCase(Protocol):
    async def execute(self, raw_token: str) -> User: ...

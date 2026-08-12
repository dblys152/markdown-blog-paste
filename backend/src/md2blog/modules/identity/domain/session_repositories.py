from typing import Protocol

from md2blog.modules.identity.domain.auth_session import AuthSession


class AuthSessionRepository(Protocol):
    async def add(self, session: AuthSession) -> None: ...

    async def find_by_token_hash(self, token_hash: str) -> AuthSession | None: ...

    async def replace(self, previous: AuthSession, replacement: AuthSession) -> None: ...

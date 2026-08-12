from datetime import UTC, datetime, timedelta

import pytest

from md2blog.modules.identity.application.port.outbound.security import RefreshToken
from md2blog.modules.identity.application.service.refresh import (
    RefreshSessionService,
    SessionMetadata,
)
from md2blog.modules.identity.domain.auth_session import (
    AuthSession,
    InvalidRefreshSessionError,
)
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.shared.domain.tsid import TSID


class Sessions:
    def __init__(self) -> None:
        self.current: AuthSession | None = None

    async def add(self, session: AuthSession) -> None:
        self.current = session

    async def find_by_token_hash(self, token_hash: str) -> AuthSession | None:
        if self.current and self.current.refresh_token_hash == token_hash:
            return self.current
        return None

    async def replace(self, previous: AuthSession, replacement: AuthSession) -> None:
        assert previous.revoked_at is not None
        self.current = replacement


class Users:
    def __init__(self, user: User) -> None:
        self.user = user

    async def exists_by_email(self, email: Email) -> bool:
        return self.user.email == email

    async def add(self, user: User) -> None:
        self.user = user

    async def find_by_id(self, user_id: int) -> User | None:
        return self.user if self.user.id.value == user_id else None


class Tokens:
    def __init__(self) -> None:
        self.sequence = 0

    def generate(self) -> RefreshToken:
        self.sequence += 1
        return RefreshToken(f"raw-{self.sequence}", f"hash-{self.sequence}")

    def hash(self, raw_token: str) -> str:
        return raw_token.replace("raw", "hash")


class AccessTokens:
    def issue(self, user: User) -> str:
        return f"access:{user.id}"


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


def make_user() -> User:
    return User(
        id=TSID(10),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash"),
        display_name=DisplayName("User"),
    )


async def test_refresh_rotates_token_and_rejects_reuse() -> None:
    now = datetime.now(UTC)
    sessions = Sessions()
    service = RefreshSessionService(
        sessions,
        Users(make_user()),
        Tokens(),
        AccessTokens(),
        FixedClock(now),
        timedelta(days=14),
    )
    created = await service.create(make_user(), SessionMetadata(None, None))

    rotated = await service.rotate(created.refresh_token, SessionMetadata("agent", "127.0.0.1"))

    assert rotated.refresh_token == "raw-2"
    assert sessions.current is not None
    assert sessions.current.user_agent == "agent"
    with pytest.raises(InvalidRefreshSessionError):
        await service.rotate(created.refresh_token, SessionMetadata(None, None))

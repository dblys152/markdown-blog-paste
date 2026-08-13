from datetime import UTC, datetime, timedelta

import pytest

from md2blog.modules.identity.application.port.outbound.security import RefreshToken
from md2blog.modules.identity.application.service.refresh import (
    RefreshSessionService,
    SessionMetadata,
)
from md2blog.modules.identity.domain.auth_session import (
    AuthSession,
    RefreshTokenReuseDetectedError,
)
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.shared.domain.tsid import TSID


class Sessions:
    def __init__(self) -> None:
        self.items: dict[str, AuthSession] = {}

    @property
    def current(self) -> AuthSession | None:
        return next(reversed(self.items.values()), None)

    async def add(self, session: AuthSession) -> None:
        self.items[session.refresh_token_hash] = session

    async def find_by_token_hash(self, token_hash: str) -> AuthSession | None:
        return self.items.get(token_hash)

    async def find_by_token_hash_for_update(self, token_hash: str) -> AuthSession | None:
        return self.items.get(token_hash)

    async def replace(self, previous: AuthSession, replacement: AuthSession) -> None:
        assert previous.revoked_at is not None
        self.items[previous.refresh_token_hash] = previous
        self.items[replacement.refresh_token_hash] = replacement

    async def revoke(self, session: AuthSession) -> None:
        self.items[session.refresh_token_hash] = session

    async def revoke_all_by_user_id(self, user_id: TSID, revoked_at: datetime) -> None:
        self.items = {
            token_hash: session.revoke(revoked_at) if session.user_id == user_id else session
            for token_hash, session in self.items.items()
        }


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
    with pytest.raises(RefreshTokenReuseDetectedError):
        await service.rotate(created.refresh_token, SessionMetadata(None, None))

    assert sessions.current is not None
    assert sessions.current.revoked_at == now


async def test_reusing_old_token_revokes_entire_replacement_chain() -> None:
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
    first = await service.create(make_user(), SessionMetadata(None, None))
    second = await service.rotate(first.refresh_token, SessionMetadata(None, None))
    await service.rotate(second.refresh_token, SessionMetadata(None, None))

    with pytest.raises(RefreshTokenReuseDetectedError):
        await service.rotate(first.refresh_token, SessionMetadata(None, None))

    assert all(session.revoked_at == now for session in sessions.items.values())

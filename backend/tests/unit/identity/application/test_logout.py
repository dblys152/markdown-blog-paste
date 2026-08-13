from datetime import UTC, datetime, timedelta

from md2blog.modules.identity.application.port.outbound.security import RefreshToken
from md2blog.modules.identity.application.service.logout import LogoutSessionService
from md2blog.modules.identity.domain.auth_session import AuthSession
from md2blog.shared.domain.tsid import TSID


class Sessions:
    def __init__(self, session: AuthSession | None) -> None:
        self.session = session
        self.revoked_user_id: TSID | None = None

    async def add(self, session: AuthSession) -> None:
        self.session = session

    async def find_by_token_hash(self, token_hash: str) -> AuthSession | None:
        if self.session and self.session.refresh_token_hash == token_hash:
            return self.session
        return None

    async def replace(self, previous: AuthSession, replacement: AuthSession) -> None:
        self.session = replacement

    async def revoke(self, session: AuthSession) -> None:
        self.session = session

    async def revoke_all_by_user_id(self, user_id: TSID, revoked_at: datetime) -> None:
        self.revoked_user_id = user_id
        if self.session and self.session.user_id == user_id:
            self.session = self.session.revoke(revoked_at)


class Tokens:
    def generate(self) -> RefreshToken:
        return RefreshToken("raw", "hash")

    def hash(self, raw_token: str) -> str:
        return f"hash:{raw_token}"


class Clock:
    def __init__(self, now: datetime) -> None:
        self.now_value = now

    def now(self) -> datetime:
        return self.now_value


async def test_logout_revokes_current_session() -> None:
    now = datetime.now(UTC)
    sessions = Sessions(
        AuthSession(
            id=TSID(1),
            user_id=TSID(2),
            refresh_token_hash="hash:raw-token",
            expires_at=now + timedelta(days=1),
            created_at=now,
        )
    )
    service = LogoutSessionService(sessions, Tokens(), Clock(now))

    await service.logout("raw-token")

    assert sessions.session is not None
    assert sessions.session.revoked_at == now


async def test_logout_is_idempotent_without_session() -> None:
    service = LogoutSessionService(Sessions(None), Tokens(), Clock(datetime.now(UTC)))

    await service.logout(None)
    await service.logout("unknown")


async def test_logout_all_revokes_user_sessions() -> None:
    now = datetime.now(UTC)
    sessions = Sessions(None)
    service = LogoutSessionService(sessions, Tokens(), Clock(now))

    await service.logout_all(TSID(2))

    assert sessions.revoked_user_id == TSID(2)

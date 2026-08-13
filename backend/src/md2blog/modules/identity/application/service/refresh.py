from dataclasses import dataclass
from datetime import datetime, timedelta

from md2blog.modules.identity.application.port.outbound.security import (
    AccessTokenIssuer,
    Clock,
    RefreshTokenManager,
)
from md2blog.modules.identity.domain.auth_session import (
    AuthSession,
    InvalidRefreshSessionError,
    RefreshTokenReuseDetectedError,
)
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.session_repositories import AuthSessionRepository
from md2blog.modules.identity.domain.user import User
from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class SessionMetadata:
    user_agent: str | None
    ip_address: str | None


@dataclass(frozen=True, slots=True)
class TokenPairResult:
    user: User
    access_token: str
    refresh_token: str


class RefreshSessionService:
    def __init__(
        self,
        sessions: AuthSessionRepository,
        users: UserRepository,
        refresh_tokens: RefreshTokenManager,
        access_tokens: AccessTokenIssuer,
        clock: Clock,
        refresh_ttl: timedelta,
    ) -> None:
        self._sessions = sessions
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._access_tokens = access_tokens
        self._clock = clock
        self._refresh_ttl = refresh_ttl

    async def create(self, user: User, metadata: SessionMetadata) -> TokenPairResult:
        now = self._clock.now()
        token = self._refresh_tokens.generate()
        await self._sessions.add(
            AuthSession(
                id=TSID.generate(),
                user_id=user.id,
                refresh_token_hash=token.token_hash,
                expires_at=now + self._refresh_ttl,
                created_at=now,
                user_agent=metadata.user_agent,
                ip_address=metadata.ip_address,
            )
        )
        return TokenPairResult(user, self._access_tokens.issue(user), token.raw)

    async def rotate(self, raw_token: str, metadata: SessionMetadata) -> TokenPairResult:
        now = self._clock.now()
        token_hash = self._refresh_tokens.hash(raw_token)
        previous = await self._sessions.find_by_token_hash_for_update(token_hash)
        if previous is None:
            raise InvalidRefreshSessionError
        if not previous.is_active(now):
            if previous.replaced_by_token_hash is not None:
                await self._revoke_replacement_chain(previous.replaced_by_token_hash, now)
                raise RefreshTokenReuseDetectedError
            raise InvalidRefreshSessionError

        user = await self._users.find_by_id(previous.user_id.value)
        if user is None:
            raise InvalidRefreshSessionError

        replacement_token = self._refresh_tokens.generate()
        rotated_previous = previous.rotate(
            now=now,
            replacement_hash=replacement_token.token_hash,
        )
        replacement = AuthSession(
            id=TSID.generate(),
            user_id=user.id,
            refresh_token_hash=replacement_token.token_hash,
            expires_at=now + self._refresh_ttl,
            created_at=now,
            user_agent=metadata.user_agent,
            ip_address=metadata.ip_address,
        )
        await self._sessions.replace(rotated_previous, replacement)
        return TokenPairResult(user, self._access_tokens.issue(user), replacement_token.raw)

    async def _revoke_replacement_chain(self, token_hash: str, now: datetime) -> None:
        current_hash: str | None = token_hash
        while current_hash is not None:
            session = await self._sessions.find_by_token_hash_for_update(current_hash)
            if session is None:
                return
            await self._sessions.revoke(session.revoke(now))
            current_hash = session.replaced_by_token_hash

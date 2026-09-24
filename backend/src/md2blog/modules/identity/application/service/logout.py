from md2blog.modules.identity.application.port.outbound.security import (
    Clock,
    RefreshTokenManager,
)
from md2blog.modules.identity.domain.events import AllSessionsRevoked
from md2blog.modules.identity.domain.session_repositories import AuthSessionRepository
from md2blog.shared.application.events import DomainEventPublisher
from md2blog.shared.domain.tsid import TSID


class LogoutSessionService:
    def __init__(
        self,
        sessions: AuthSessionRepository,
        refresh_tokens: RefreshTokenManager,
        clock: Clock,
        events: DomainEventPublisher,
    ) -> None:
        self._sessions = sessions
        self._refresh_tokens = refresh_tokens
        self._clock = clock
        self._events = events

    async def logout(self, raw_token: str | None) -> None:
        if raw_token is None:
            return
        token_hash = self._refresh_tokens.hash(raw_token)
        session = await self._sessions.find_by_token_hash(token_hash)
        if session is None:
            return
        await self._sessions.revoke(session.revoke(self._clock.now()))

    async def logout_all(self, user_id: TSID) -> None:
        now = self._clock.now()
        await self._sessions.revoke_all_by_user_id(user_id, now)
        await self._events.publish(
            AllSessionsRevoked(
                event_id=TSID.generate(),
                aggregate_id=user_id,
                occurred_at=now,
                user_id=user_id,
            )
        )

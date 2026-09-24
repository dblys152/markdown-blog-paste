from dataclasses import dataclass
from datetime import timedelta

from md2blog.modules.identity.application.port.outbound.account_confirmation_token import (
    AccountConfirmationTokenManager,
)
from md2blog.modules.identity.application.port.outbound.security import Clock, PasswordHasher
from md2blog.modules.identity.domain.account_confirmation_token import (
    AccountConfirmationToken,
    AccountConfirmationTokenExpiredError,
    AccountConfirmationTokenPurpose,
    AccountConfirmationTokenUnavailableError,
)
from md2blog.modules.identity.domain.account_confirmation_token_repositories import (
    AccountConfirmationTokenRepository,
)
from md2blog.modules.identity.domain.commands import (
    ConfirmPasswordResetCommand,
    RequestPasswordResetCommand,
)
from md2blog.modules.identity.domain.events import (
    AllSessionsRevoked,
    PasswordResetCompleted,
    PasswordResetRequested,
)
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.session_repositories import AuthSessionRepository
from md2blog.shared.application.events import DomainEventPublisher
from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class PasswordResetPolicy:
    token_ttl: timedelta = timedelta(minutes=60)
    resend_cooldown: timedelta = timedelta(seconds=60)
    daily_limit: int = 5


class RequestPasswordReset:
    def __init__(
        self,
        *,
        users: UserRepository,
        tokens: AccountConfirmationTokenRepository,
        token_manager: AccountConfirmationTokenManager,
        events: DomainEventPublisher,
        clock: Clock,
        policy: PasswordResetPolicy,
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._token_manager = token_manager
        self._events = events
        self._clock = clock
        self._policy = policy

    async def execute(self, command: RequestPasswordResetCommand) -> None:
        user = await self._users.find_by_email(command.email)
        if user is None:
            return

        now = self._clock.now()
        latest = await self._tokens.find_latest_by_user_id(user.id)
        if latest is not None and latest.created_at + self._policy.resend_cooldown > now:
            return
        recent_request_count = await self._tokens.count_created_since(
            user.id,
            now - timedelta(days=1),
        )
        if recent_request_count >= self._policy.daily_limit:
            return

        if latest is not None and latest.is_active(now):
            await self._tokens.save(latest.revoke(now))

        generated = self._token_manager.generate()
        token = AccountConfirmationToken.issue(
            token_id=TSID.generate(),
            user_id=user.id,
            purpose=AccountConfirmationTokenPurpose.PASSWORD_RESET,
            token_hash=generated.token_hash,
            issued_at=now,
            expires_at=now + self._policy.token_ttl,
        )
        await self._tokens.add(token)
        await self._events.publish(
            PasswordResetRequested(
                event_id=TSID.generate(),
                aggregate_id=user.id,
                occurred_at=now,
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                raw_token=generated.raw,
            )
        )


class ConfirmPasswordReset:
    def __init__(
        self,
        *,
        users: UserRepository,
        sessions: AuthSessionRepository,
        tokens: AccountConfirmationTokenRepository,
        token_manager: AccountConfirmationTokenManager,
        password_hasher: PasswordHasher,
        events: DomainEventPublisher,
        clock: Clock,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._tokens = tokens
        self._token_manager = token_manager
        self._password_hasher = password_hasher
        self._events = events
        self._clock = clock

    async def execute(self, command: ConfirmPasswordResetCommand) -> None:
        token = await self._tokens.find_by_token_hash_for_update(
            self._token_manager.hash(command.token)
        )
        if token is None or token.purpose != AccountConfirmationTokenPurpose.PASSWORD_RESET:
            raise InvalidPasswordResetTokenError

        now = self._clock.now()
        try:
            used_token = token.use(now)
        except (
            AccountConfirmationTokenExpiredError,
            AccountConfirmationTokenUnavailableError,
        ) as exc:
            raise InvalidPasswordResetTokenError from exc
        user = await self._users.find_by_id(token.user_id.value)
        if user is None:
            raise InvalidPasswordResetTokenError

        password_hash = self._password_hasher.hash(command.new_password)
        await self._users.save(user.reset_password(password_hash, now))
        await self._tokens.save(used_token)
        await self._sessions.revoke_all_by_user_id(user.id, now)
        await self._events.publish(
            PasswordResetCompleted(
                event_id=TSID.generate(),
                aggregate_id=user.id,
                occurred_at=now,
                user_id=user.id,
            )
        )
        await self._events.publish(
            AllSessionsRevoked(
                event_id=TSID.generate(),
                aggregate_id=user.id,
                occurred_at=now,
                user_id=user.id,
            )
        )


class InvalidPasswordResetTokenError(Exception):
    pass

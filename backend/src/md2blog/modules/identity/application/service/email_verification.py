from dataclasses import dataclass
from datetime import timedelta

from md2blog.modules.identity.application.port.outbound.account_confirmation_token import (
    AccountConfirmationTokenManager,
)
from md2blog.modules.identity.application.port.outbound.security import Clock
from md2blog.modules.identity.domain.account_confirmation_token import (
    AccountConfirmationToken,
    AccountConfirmationTokenExpiredError,
    AccountConfirmationTokenPurpose,
    AccountConfirmationTokenUnavailableError,
)
from md2blog.modules.identity.domain.account_confirmation_token_repositories import (
    AccountConfirmationTokenRepository,
)
from md2blog.modules.identity.domain.events import EmailVerificationRequested, EmailVerified
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.user import User
from md2blog.shared.application.events import DomainEventPublisher
from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class EmailVerificationPolicy:
    token_ttl: timedelta = timedelta(hours=24)
    resend_cooldown: timedelta = timedelta(seconds=60)
    daily_limit: int = 5


class IssueEmailVerification:
    def __init__(
        self,
        *,
        tokens: AccountConfirmationTokenRepository,
        token_manager: AccountConfirmationTokenManager,
        events: DomainEventPublisher,
        clock: Clock,
        policy: EmailVerificationPolicy,
    ) -> None:
        self._tokens = tokens
        self._token_manager = token_manager
        self._events = events
        self._clock = clock
        self._policy = policy

    async def execute(self, user: User) -> None:
        if user.is_email_verified:
            return

        now = self._clock.now()
        latest = await self._tokens.find_latest_by_user_id(user.id)
        if latest is not None and latest.created_at + self._policy.resend_cooldown > now:
            retry_after = latest.created_at + self._policy.resend_cooldown - now
            raise EmailVerificationCooldownError(max(1, int(retry_after.total_seconds())))

        since = now - timedelta(days=1)
        if await self._tokens.count_created_since(user.id, since) >= self._policy.daily_limit:
            raise EmailVerificationDailyLimitError

        if latest is not None and latest.is_active(now):
            await self._tokens.save(latest.revoke(now))

        generated = self._token_manager.generate()
        token = AccountConfirmationToken.issue(
            token_id=TSID.generate(),
            user_id=user.id,
            purpose=AccountConfirmationTokenPurpose.EMAIL_VERIFICATION,
            token_hash=generated.token_hash,
            issued_at=now,
            expires_at=now + self._policy.token_ttl,
        )
        await self._tokens.add(token)
        await self._events.publish(
            EmailVerificationRequested(
                event_id=TSID.generate(),
                aggregate_id=user.id,
                occurred_at=now,
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                raw_token=generated.raw,
            )
        )


class ConfirmEmailVerification:
    def __init__(
        self,
        *,
        users: UserRepository,
        tokens: AccountConfirmationTokenRepository,
        token_manager: AccountConfirmationTokenManager,
        events: DomainEventPublisher,
        clock: Clock,
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._token_manager = token_manager
        self._events = events
        self._clock = clock

    async def execute(self, raw_token: str) -> User:
        token_hash = self._token_manager.hash(raw_token)
        token = await self._tokens.find_by_token_hash_for_update(token_hash)
        if token is None or token.purpose != AccountConfirmationTokenPurpose.EMAIL_VERIFICATION:
            raise InvalidEmailVerificationTokenError

        now = self._clock.now()
        try:
            confirmed_token = token.use(now)
        except (
            AccountConfirmationTokenExpiredError,
            AccountConfirmationTokenUnavailableError,
        ) as exc:
            raise InvalidEmailVerificationTokenError from exc
        user = await self._users.find_by_id(token.user_id.value)
        if user is None:
            raise InvalidEmailVerificationTokenError

        verified_user = user.verify_email(now)
        await self._tokens.save(confirmed_token)
        await self._users.save(verified_user)
        await self._events.publish(
            EmailVerified(
                event_id=TSID.generate(),
                aggregate_id=user.id,
                occurred_at=now,
                user_id=user.id,
            )
        )
        return verified_user


class EmailVerificationCooldownError(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__("email verification resend cooldown")


class EmailVerificationDailyLimitError(Exception):
    pass


class InvalidEmailVerificationTokenError(Exception):
    pass

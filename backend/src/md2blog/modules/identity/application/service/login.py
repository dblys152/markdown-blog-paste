from dataclasses import dataclass
from datetime import datetime
from typing import NoReturn

from md2blog.modules.identity.application.port.outbound.security import (
    Clock,
    PasswordHasher,
)
from md2blog.modules.identity.domain.commands import LoginCommand
from md2blog.modules.identity.domain.events import AuthenticationFailed, AuthenticationSucceeded
from md2blog.modules.identity.domain.login_failure_state import (
    LoginFailurePolicy,
    LoginFailureState,
    LoginRateLimitedError,
)
from md2blog.modules.identity.domain.login_failure_state_repositories import (
    LoginFailureStateRepository,
)
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.user import AuthenticationFailedError, User
from md2blog.shared.application.events import DomainEventPublisher
from md2blog.shared.domain.tsid import TSID


@dataclass(frozen=True, slots=True)
class LoginResult:
    user: User


class Login:
    def __init__(
        self,
        users: UserRepository,
        password_hasher: PasswordHasher,
        failures: LoginFailureStateRepository,
        clock: Clock,
        policy: LoginFailurePolicy,
        events: DomainEventPublisher,
    ) -> None:
        self._users = users
        self._password_hasher = password_hasher
        self._failures = failures
        self._clock = clock
        self._policy = policy
        self._events = events

    async def execute(self, command: LoginCommand) -> LoginResult:
        user = await self._users.find_by_email(command.email)
        if user is None:
            raise AuthenticationFailedError

        now = self._clock.now()
        failure = await self._failures.find_for_update(user.id)
        retry_after = failure.retry_after_seconds(now) if failure is not None else 0
        if retry_after > 0:
            raise LoginRateLimitedError(retry_after)

        if user.password_hash is None:
            await self._publish_failure(user.id, now)
            raise AuthenticationFailedError

        password_matches = self._password_hasher.verify(
            command.password,
            user.password_hash,
        )
        try:
            user.authenticate(password_matches)
        except AuthenticationFailedError:
            await self._record_failure(user.id, failure, now)

        await self._failures.delete(user.id)
        await self._events.publish(
            AuthenticationSucceeded(
                event_id=TSID.generate(),
                aggregate_id=user.id,
                occurred_at=now,
                user_id=user.id,
            )
        )
        return LoginResult(user=user)

    async def _record_failure(
        self,
        user_id: TSID,
        failure: LoginFailureState | None,
        now: datetime,
    ) -> NoReturn:
        if failure is None:
            failure = LoginFailureState.first_failure(user_id, now)
            await self._failures.add(failure)
        else:
            failure.record_failure(now, self._policy)
            await self._failures.save(failure)
        await self._publish_failure(user_id, now)
        retry_after = failure.retry_after_seconds(now)
        if retry_after > 0:
            raise LoginRateLimitedError(retry_after)
        raise AuthenticationFailedError

    async def _publish_failure(self, user_id: TSID, occurred_at: datetime) -> None:
        await self._events.publish(
            AuthenticationFailed(
                event_id=TSID.generate(),
                aggregate_id=user_id,
                occurred_at=occurred_at,
                user_id=user_id,
            )
        )

from dataclasses import dataclass
from datetime import datetime
from typing import NoReturn

from md2blog.modules.identity.application.port.outbound.security import (
    Clock,
    PasswordHasher,
)
from md2blog.modules.identity.domain.commands import LoginCommand
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
    ) -> None:
        self._users = users
        self._password_hasher = password_hasher
        self._failures = failures
        self._clock = clock
        self._policy = policy

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
        retry_after = failure.retry_after_seconds(now)
        if retry_after > 0:
            raise LoginRateLimitedError(retry_after)
        raise AuthenticationFailedError

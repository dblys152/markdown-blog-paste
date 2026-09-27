from dataclasses import dataclass

from md2blog.modules.identity.application.port.inbound.email_verification import (
    IssueEmailVerificationUseCase,
)
from md2blog.modules.identity.application.port.outbound.security import AccessTokenIssuer, Clock
from md2blog.modules.identity.domain.commands import SignUpCommand
from md2blog.modules.identity.domain.nickname_policy import NicknameUniquenessPolicy
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.user import User
from md2blog.shared.application.unit_of_work import UnitOfWork


class EmailAlreadyExistsError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class SignUpResult:
    user: User
    access_token: str


class SignUp:
    def __init__(
        self,
        users: UserRepository,
        token_issuer: AccessTokenIssuer,
        email_verification: IssueEmailVerificationUseCase,
        nickname_policy: NicknameUniquenessPolicy,
        clock: Clock,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._users = users
        self._token_issuer = token_issuer
        self._email_verification = email_verification
        self._nickname_policy = nickname_policy
        self._clock = clock
        self._unit_of_work = unit_of_work

    async def execute(self, command: SignUpCommand) -> SignUpResult:
        async with self._unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: SignUpCommand) -> SignUpResult:
        self._nickname_policy.ensure_available(
            is_already_used=await self._users.exists_by_display_name(command.display_name)
        )
        user = User.sign_up(command, self._clock.now())
        await self._users.add(user)
        await self._email_verification.execute(user)
        return SignUpResult(user=user, access_token=self._token_issuer.issue(user))

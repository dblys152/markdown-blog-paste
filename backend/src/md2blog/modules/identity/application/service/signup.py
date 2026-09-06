from dataclasses import dataclass

from md2blog.modules.identity.application.port.inbound.email_verification import (
    IssueEmailVerificationUseCase,
)
from md2blog.modules.identity.application.port.outbound.security import AccessTokenIssuer
from md2blog.modules.identity.domain.commands import SignUpCommand
from md2blog.modules.identity.domain.nickname_policy import NicknameUniquenessPolicy
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.user import User


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
    ) -> None:
        self._users = users
        self._token_issuer = token_issuer
        self._email_verification = email_verification
        self._nickname_policy = nickname_policy

    async def execute(self, command: SignUpCommand) -> SignUpResult:
        self._nickname_policy.ensure_available(
            is_already_used=await self._users.exists_by_display_name(
                command.display_name
            )
        )
        user = User.sign_up(command)
        await self._users.add(user)
        await self._email_verification.execute(user)
        return SignUpResult(user=user, access_token=self._token_issuer.issue(user))

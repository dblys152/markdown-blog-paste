from dataclasses import dataclass

from md2blog.modules.identity.application.port.inbound.email_verification import (
    IssueEmailVerificationUseCase,
)
from md2blog.modules.identity.application.port.outbound.security import AccessTokenIssuer
from md2blog.modules.identity.domain.commands import SignUpCommand
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
    ) -> None:
        self._users = users
        self._token_issuer = token_issuer
        self._email_verification = email_verification

    async def execute(self, command: SignUpCommand) -> SignUpResult:
        user = User.sign_up(command)
        await self._users.add(user)
        await self._email_verification.execute(user)
        return SignUpResult(user=user, access_token=self._token_issuer.issue(user))

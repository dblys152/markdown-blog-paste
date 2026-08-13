from dataclasses import dataclass

from md2blog.modules.identity.application.port.outbound.security import PasswordHasher
from md2blog.modules.identity.domain.commands import LoginCommand
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.user import AuthenticationFailedError, User


@dataclass(frozen=True, slots=True)
class LoginResult:
    user: User


class Login:
    def __init__(self, users: UserRepository, password_hasher: PasswordHasher) -> None:
        self._users = users
        self._password_hasher = password_hasher

    async def execute(self, command: LoginCommand) -> LoginResult:
        user = await self._users.find_by_email(command.email)
        if user is None:
            raise AuthenticationFailedError

        password_matches = self._password_hasher.verify(
            command.password,
            user.password_hash,
        )
        user.authenticate(password_matches)
        return LoginResult(user=user)

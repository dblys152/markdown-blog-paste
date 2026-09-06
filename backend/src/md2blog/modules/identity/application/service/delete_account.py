from md2blog.modules.identity.application.port.outbound.security import PasswordHasher
from md2blog.modules.identity.domain.commands import DeleteAccountCommand
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.user import User


class DeleteAccount:
    def __init__(self, users: UserRepository, password_hasher: PasswordHasher) -> None:
        self._users = users
        self._password_hasher = password_hasher

    async def execute(self, user: User, command: DeleteAccountCommand) -> None:
        password_matches = self._password_hasher.verify(
            command.password,
            user.password_hash,
        )
        user.confirm_account_deletion(password_matches)
        await self._users.delete(user)

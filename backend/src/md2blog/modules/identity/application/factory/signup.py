from md2blog.modules.identity.application.port.inbound.signup import SignUpRequest
from md2blog.modules.identity.application.port.outbound.security import PasswordHasher
from md2blog.modules.identity.application.service.signup import EmailAlreadyExistsError
from md2blog.modules.identity.domain.commands import SignUpCommand
from md2blog.modules.identity.domain.repositories import UserRepository
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, RawPassword
from md2blog.shared.domain.tsid import TSID


class SignUpCommandFactory:
    def __init__(self, users: UserRepository, password_hasher: PasswordHasher) -> None:
        self._users = users
        self._password_hasher = password_hasher

    async def create(self, request: SignUpRequest) -> SignUpCommand:
        email = Email(str(request.email))
        if await self._users.exists_by_email(email):
            raise EmailAlreadyExistsError

        return SignUpCommand(
            id=TSID.generate(),
            email=email,
            password_hash=self._password_hasher.hash(RawPassword(request.password)),
            display_name=DisplayName(request.display_name),
        )

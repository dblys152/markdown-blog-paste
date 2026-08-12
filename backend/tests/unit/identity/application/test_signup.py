from md2blog.modules.identity.application.factory.signup import SignUpCommandFactory
from md2blog.modules.identity.application.port.inbound.signup import SignUpRequest
from md2blog.modules.identity.application.service.signup import SignUp
from md2blog.modules.identity.domain.commands import SignUpCommand
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import (
    DisplayName,
    Email,
    PasswordHash,
    RawPassword,
)
from md2blog.shared.domain.tsid import TSID


class InMemoryUsers:
    def __init__(self) -> None:
        self.user: User | None = None

    async def exists_by_email(self, email: Email) -> bool:
        return self.user is not None and self.user.email == email

    async def add(self, user: User) -> None:
        self.user = user


class StubPasswordHasher:
    def hash(self, password: RawPassword) -> PasswordHash:
        return PasswordHash(f"hashed:{password.value}")


class StubTokenIssuer:
    def issue(self, user: User) -> str:
        return f"token:{user.id}"


async def test_signup_factory_builds_domain_command_and_service_stores_user() -> None:
    users = InMemoryUsers()
    factory = SignUpCommandFactory(users, StubPasswordHasher())
    service = SignUp(users, StubTokenIssuer())

    command = await factory.create(
        SignUpRequest(
            email="User@Example.com",
            password="strong-password",
            display_name=" Youngseok ",
        )
    )
    result = await service.execute(command)

    assert users.user == result.user
    assert result.user.email == Email("user@example.com")
    assert result.user.password_hash == PasswordHash("hashed:strong-password")
    assert result.user.display_name == DisplayName("Youngseok")
    assert result.access_token == f"token:{result.user.id}"


def test_user_signs_up_from_domain_command() -> None:
    user_id = TSID(1)
    command = SignUpCommand(
        id=user_id,
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash"),
        display_name=DisplayName("User"),
    )

    user = User.sign_up(command)

    assert user.id == user_id

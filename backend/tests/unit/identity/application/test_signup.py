import pytest

from md2blog.modules.identity.application.factory.signup import SignUpCommandFactory
from md2blog.modules.identity.application.port.inbound.signup import SignUpRequest
from md2blog.modules.identity.application.service.signup import SignUp
from md2blog.modules.identity.domain.commands import SignUpCommand
from md2blog.modules.identity.domain.nickname_policy import (
    NicknameAlreadyInUseError,
    NicknameUniquenessPolicy,
)
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

    async def exists_by_display_name(
        self,
        display_name: DisplayName,
        *,
        exclude_user_id: TSID | None = None,
    ) -> bool:
        return self.user is not None and self.user.display_name == display_name

    async def add(self, user: User) -> None:
        self.user = user


class StubPasswordHasher:
    def hash(self, password: RawPassword) -> PasswordHash:
        return PasswordHash(f"hashed:{password.value}")


class StubTokenIssuer:
    def issue(self, user: User) -> str:
        return f"token:{user.id}"


class RecordingEmailVerification:
    def __init__(self) -> None:
        self.user: User | None = None

    async def execute(self, user: User) -> None:
        self.user = user


async def test_signup_factory_builds_domain_command_and_service_stores_user() -> None:
    users = InMemoryUsers()
    factory = SignUpCommandFactory(users, StubPasswordHasher())
    email_verification = RecordingEmailVerification()
    service = SignUp(
        users,
        StubTokenIssuer(),
        email_verification,
        NicknameUniquenessPolicy(),
    )

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
    assert email_verification.user == result.user


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


async def test_signup_service_rejects_duplicate_nickname() -> None:
    users = InMemoryUsers()
    users.user = User(
        id=TSID(1),
        email=Email("other@example.com"),
        password_hash=PasswordHash("hash"),
        display_name=DisplayName("Youngseok"),
    )
    factory = SignUpCommandFactory(users, StubPasswordHasher())

    command = await factory.create(
        SignUpRequest(
            email="new@example.com",
            password="strong-password",
            display_name="Youngseok",
        )
    )

    with pytest.raises(NicknameAlreadyInUseError):
        await SignUp(
            users,
            StubTokenIssuer(),
            RecordingEmailVerification(),
            NicknameUniquenessPolicy(),
        ).execute(command)

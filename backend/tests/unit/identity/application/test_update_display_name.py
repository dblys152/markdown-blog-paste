import pytest

from md2blog.modules.identity.application.service.update_display_name import UpdateDisplayName
from md2blog.modules.identity.domain.commands import UpdateDisplayNameCommand
from md2blog.modules.identity.domain.nickname_policy import (
    NicknameAlreadyInUseError,
    NicknameUniquenessPolicy,
)
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, PasswordHash
from md2blog.shared.domain.tsid import TSID


class Users:
    def __init__(self, existing_display_name: DisplayName | None = None) -> None:
        self.saved: User | None = None
        self.existing_display_name = existing_display_name

    async def exists_by_display_name(
        self,
        display_name: DisplayName,
        *,
        exclude_user_id: TSID | None = None,
    ) -> bool:
        return (
            self.existing_display_name is not None
            and self.existing_display_name.value.lower() == display_name.value.lower()
        )

    async def save(self, user: User) -> None:
        self.saved = user


async def test_update_display_name_saves_changed_user() -> None:
    users = Users()
    user = User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash"),
        display_name=DisplayName("기존 이름"),
    )

    updated_user = await UpdateDisplayName(users, NicknameUniquenessPolicy()).execute(
        user,
        UpdateDisplayNameCommand(display_name=DisplayName("새 이름")),
    )

    assert updated_user.display_name == DisplayName("새 이름")
    assert users.saved == updated_user


async def test_update_display_name_skips_save_when_name_is_unchanged() -> None:
    users = Users()
    user = User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash"),
        display_name=DisplayName("같은 이름"),
    )

    updated_user = await UpdateDisplayName(users, NicknameUniquenessPolicy()).execute(
        user,
        UpdateDisplayNameCommand(display_name=DisplayName("같은 이름")),
    )

    assert updated_user is user
    assert users.saved is None


async def test_update_display_name_rejects_duplicate_case_insensitively() -> None:
    users = Users(existing_display_name=DisplayName("Existing"))
    user = User(
        id=TSID(1),
        email=Email("user@example.com"),
        password_hash=PasswordHash("hash"),
        display_name=DisplayName("기존 이름"),
    )

    with pytest.raises(NicknameAlreadyInUseError):
        await UpdateDisplayName(users, NicknameUniquenessPolicy()).execute(
            user,
            UpdateDisplayNameCommand(display_name=DisplayName("existing")),
        )

    assert users.saved is None

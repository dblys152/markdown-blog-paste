import pytest

from md2blog.modules.identity.domain.nickname_policy import (
    NicknameAlreadyInUseError,
    NicknameUniquenessPolicy,
)


def test_available_nickname_is_allowed() -> None:
    NicknameUniquenessPolicy().ensure_available(is_already_used=False)


def test_already_used_nickname_is_rejected() -> None:
    with pytest.raises(NicknameAlreadyInUseError):
        NicknameUniquenessPolicy().ensure_available(is_already_used=True)

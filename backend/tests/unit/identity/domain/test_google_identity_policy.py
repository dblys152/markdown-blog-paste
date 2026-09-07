import pytest

from md2blog.modules.identity.domain.google_identity_policy import (
    GoogleIdentityAlreadyLinkedError,
    GoogleIdentityLinkPolicy,
    GoogleIdentityNotLinkedError,
    GoogleIdentityUnlinkPolicy,
    LastSignInMethodError,
)


def test_google_identity_can_be_linked_when_both_sides_are_available() -> None:
    GoogleIdentityLinkPolicy().ensure_linkable(
        linked_to_another_user=False,
        user_already_has_google=False,
    )


@pytest.mark.parametrize("another,own", [(True, False), (False, True)])
def test_google_identity_cannot_be_linked_twice(another: bool, own: bool) -> None:
    with pytest.raises(GoogleIdentityAlreadyLinkedError):
        GoogleIdentityLinkPolicy().ensure_linkable(
            linked_to_another_user=another,
            user_already_has_google=own,
        )


def test_google_identity_can_be_unlinked_when_password_remains() -> None:
    GoogleIdentityUnlinkPolicy().ensure_unlinkable(is_linked=True, has_password=True)


def test_missing_google_identity_cannot_be_unlinked() -> None:
    with pytest.raises(GoogleIdentityNotLinkedError):
        GoogleIdentityUnlinkPolicy().ensure_unlinkable(is_linked=False, has_password=True)


def test_last_sign_in_method_cannot_be_unlinked() -> None:
    with pytest.raises(LastSignInMethodError):
        GoogleIdentityUnlinkPolicy().ensure_unlinkable(is_linked=True, has_password=False)

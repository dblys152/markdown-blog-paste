class GoogleIdentityAlreadyLinkedError(Exception):
    pass


class GoogleIdentityNotLinkedError(Exception):
    pass


class LastSignInMethodError(Exception):
    pass


class GoogleIdentityLinkPolicy:
    def ensure_linkable(
        self,
        *,
        linked_to_another_user: bool,
        user_already_has_google: bool,
    ) -> None:
        if linked_to_another_user or user_already_has_google:
            raise GoogleIdentityAlreadyLinkedError


class GoogleIdentityUnlinkPolicy:
    def ensure_unlinkable(self, *, is_linked: bool, has_password: bool) -> None:
        if not is_linked:
            raise GoogleIdentityNotLinkedError
        if not has_password:
            raise LastSignInMethodError

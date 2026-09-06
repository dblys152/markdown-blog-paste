class NicknameAlreadyInUseError(Exception):
    pass


class NicknameUniquenessPolicy:
    def ensure_available(self, *, is_already_used: bool) -> None:
        if is_already_used:
            raise NicknameAlreadyInUseError

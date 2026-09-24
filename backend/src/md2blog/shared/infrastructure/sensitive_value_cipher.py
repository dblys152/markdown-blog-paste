from cryptography.fernet import Fernet, InvalidToken


class FernetSensitiveValueCipher:
    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode("ascii"))

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, encrypted_value: str) -> str:
        try:
            return self._fernet.decrypt(encrypted_value.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise InvalidSensitiveValueError from exc


class InvalidSensitiveValueError(Exception):
    pass

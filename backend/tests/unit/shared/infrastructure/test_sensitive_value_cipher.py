import pytest
from cryptography.fernet import Fernet

from md2blog.shared.infrastructure.sensitive_value_cipher import (
    FernetSensitiveValueCipher,
    InvalidSensitiveValueError,
)


def test_sensitive_value_cipher_round_trip() -> None:
    cipher = FernetSensitiveValueCipher(Fernet.generate_key().decode("ascii"))

    encrypted = cipher.encrypt('{"token":"secret"}')

    assert "secret" not in encrypted
    assert cipher.decrypt(encrypted) == '{"token":"secret"}'


def test_sensitive_value_cipher_rejects_invalid_value() -> None:
    cipher = FernetSensitiveValueCipher(Fernet.generate_key().decode("ascii"))

    with pytest.raises(InvalidSensitiveValueError):
        cipher.decrypt("not-a-valid-payload")

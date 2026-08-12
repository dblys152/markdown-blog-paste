from md2blog.modules.identity.domain.value_objects import RawPassword
from md2blog.modules.identity.infrastructure.passwords import Argon2PasswordHasher


def test_password_is_hashed_with_argon2id_and_can_be_verified() -> None:
    hasher = Argon2PasswordHasher()

    password = RawPassword("strong-password")
    password_hash = hasher.hash(password)

    assert password_hash.value.startswith("$argon2id$")
    assert password_hash.value != password.value
    assert hasher.verify(password, password_hash)
    assert not hasher.verify(RawPassword("wrong-password"), password_hash)

from pwdlib import PasswordHash

from md2blog.modules.identity.domain.value_objects import (
    PasswordHash as DomainPasswordHash,
)
from md2blog.modules.identity.domain.value_objects import RawPassword


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._password_hash = PasswordHash.recommended()

    def hash(self, password: RawPassword) -> DomainPasswordHash:
        return DomainPasswordHash(self._password_hash.hash(password.value))

    def verify(self, password: RawPassword, password_hash: DomainPasswordHash) -> bool:
        return self._password_hash.verify(password.value, password_hash.value)

from typing import Protocol

from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import PasswordHash, RawPassword


class PasswordHasher(Protocol):
    def hash(self, password: RawPassword) -> PasswordHash: ...


class AccessTokenIssuer(Protocol):
    def issue(self, user: User) -> str: ...

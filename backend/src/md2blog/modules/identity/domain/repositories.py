from typing import Protocol

from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import Email


class UserRepository(Protocol):
    async def exists_by_email(self, email: Email) -> bool: ...

    async def add(self, user: User) -> None: ...

    async def find_by_id(self, user_id: int) -> User | None: ...

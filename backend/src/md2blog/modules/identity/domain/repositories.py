from typing import Protocol

from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email
from md2blog.shared.domain.tsid import TSID


class UserRepository(Protocol):
    async def exists_by_email(self, email: Email) -> bool: ...

    async def exists_by_display_name(
        self,
        display_name: DisplayName,
        *,
        exclude_user_id: TSID | None = None,
    ) -> bool: ...

    async def add(self, user: User) -> None: ...

    async def save(self, user: User) -> None: ...

    async def delete(self, user: User) -> None: ...

    async def find_by_id(self, user_id: int) -> User | None: ...

    async def find_by_email(self, email: Email) -> User | None: ...

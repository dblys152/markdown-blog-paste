from datetime import datetime
from typing import Protocol

from md2blog.modules.identity.domain.password_reset import PasswordResetToken
from md2blog.shared.domain.tsid import TSID


class PasswordResetTokenRepository(Protocol):
    async def add(self, token: PasswordResetToken) -> None: ...

    async def find_by_token_hash_for_update(
        self,
        token_hash: str,
    ) -> PasswordResetToken | None: ...

    async def find_latest_by_user_id(self, user_id: TSID) -> PasswordResetToken | None: ...

    async def save(self, token: PasswordResetToken) -> None: ...

    async def count_created_since(self, user_id: TSID, since: datetime) -> int: ...

from datetime import datetime
from typing import Protocol

from md2blog.modules.identity.domain.email_verification import EmailVerificationToken
from md2blog.shared.domain.tsid import TSID


class EmailVerificationTokenRepository(Protocol):
    async def add(self, token: EmailVerificationToken) -> None: ...

    async def find_by_token_hash_for_update(
        self,
        token_hash: str,
    ) -> EmailVerificationToken | None: ...

    async def find_latest_by_user_id(self, user_id: TSID) -> EmailVerificationToken | None: ...

    async def save(self, token: EmailVerificationToken) -> None: ...

    async def count_created_since(self, user_id: TSID, since: datetime) -> int: ...

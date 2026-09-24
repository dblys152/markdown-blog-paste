from datetime import datetime
from typing import Protocol

from md2blog.modules.identity.domain.account_confirmation_token import AccountConfirmationToken
from md2blog.shared.domain.tsid import TSID


class AccountConfirmationTokenRepository(Protocol):
    async def add(self, token: AccountConfirmationToken) -> None: ...

    async def find_by_token_hash_for_update(
        self, token_hash: str
    ) -> AccountConfirmationToken | None: ...

    async def find_latest_by_user_id(self, user_id: TSID) -> AccountConfirmationToken | None: ...

    async def save(self, token: AccountConfirmationToken) -> None: ...

    async def count_created_since(self, user_id: TSID, since: datetime) -> int: ...

from typing import Protocol

from md2blog.modules.identity.domain.user_identity import IdentityProvider, UserIdentity
from md2blog.shared.domain.tsid import TSID


class UserIdentityRepository(Protocol):
    async def add(self, identity: UserIdentity) -> None: ...

    async def delete(self, identity: UserIdentity) -> None: ...

    async def find_by_provider_subject(
        self,
        provider: IdentityProvider,
        provider_subject: str,
    ) -> UserIdentity | None: ...

    async def find_by_user_and_provider(
        self,
        user_id: TSID,
        provider: IdentityProvider,
    ) -> UserIdentity | None: ...

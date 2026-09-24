from typing import Protocol

from md2blog.modules.identity.domain.login_failure_state import LoginFailureState
from md2blog.shared.domain.tsid import TSID


class LoginFailureStateRepository(Protocol):
    async def find_for_update(self, user_id: TSID) -> LoginFailureState | None: ...

    async def add(self, state: LoginFailureState) -> None: ...

    async def save(self, state: LoginFailureState) -> None: ...

    async def delete(self, user_id: TSID) -> None: ...

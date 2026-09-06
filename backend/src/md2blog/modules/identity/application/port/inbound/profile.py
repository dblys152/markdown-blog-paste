from typing import Annotated, Protocol

from pydantic import BaseModel, StringConstraints

from md2blog.modules.identity.domain.commands import UpdateDisplayNameCommand
from md2blog.modules.identity.domain.user import User


class UpdateDisplayNameRequest(BaseModel):
    display_name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=10),
    ]


class UpdateDisplayNameUseCase(Protocol):
    async def execute(
        self,
        user: User,
        command: UpdateDisplayNameCommand,
    ) -> User: ...

from typing import Literal, Protocol

from pydantic import BaseModel, Field

from md2blog.modules.identity.application.models.google_auth import (
    GoogleConnection,
    GoogleLoginResult,
)
from md2blog.modules.identity.domain.commands import (
    GoogleSignUpCommand,
    LinkGoogleAndLoginCommand,
)
from md2blog.modules.identity.domain.user import User


class GoogleCredentialRequest(BaseModel):
    credential: str = Field(min_length=1)


class GoogleSignUpRequest(GoogleCredentialRequest):
    display_name: str = Field(min_length=1, max_length=10)


class LinkGoogleAndLoginRequest(GoogleCredentialRequest):
    password: str = Field(min_length=8, max_length=128)


class GoogleLoginFlowResponse(BaseModel):
    status: Literal["link_required", "signup_required"]
    email: str


class GoogleConnectionResponse(BaseModel):
    connected: bool
    email: str | None = None
    can_disconnect: bool = False


class GoogleLoginUseCase(Protocol):
    async def execute(self, credential: str) -> GoogleLoginResult: ...


class GoogleSignUpUseCase(Protocol):
    async def execute(self, command: GoogleSignUpCommand) -> User: ...


class LinkGoogleAndLoginUseCase(Protocol):
    async def execute(self, command: LinkGoogleAndLoginCommand) -> User: ...


class ConnectGoogleUseCase(Protocol):
    async def execute(self, user: User, credential: str) -> None: ...


class DisconnectGoogleUseCase(Protocol):
    async def execute(self, user: User) -> None: ...


class GetGoogleConnectionUseCase(Protocol):
    async def execute(self, user: User) -> GoogleConnection: ...

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError

from md2blog.modules.identity.application.port.inbound.models import TokenResponse, UserResponse
from md2blog.modules.identity.application.port.inbound.signup import SignUpRequest
from md2blog.modules.identity.application.service.refresh import (
    RefreshSessionService,
    SessionMetadata,
)
from md2blog.modules.identity.application.service.signup import EmailAlreadyExistsError
from md2blog.modules.identity.domain.auth_session import InvalidRefreshSessionError
from md2blog.modules.identity.presentation.dependencies import (
    SignUpDependencies,
    get_refresh_service,
    get_signup_dependencies,
)
from md2blog.settings import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
REFRESH_TOKEN_COOKIE = "refresh_token"


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.refresh_token_cookie_secure,
        samesite=settings.refresh_token_cookie_samesite,  # type: ignore[arg-type]
        path="/auth",
    )


def get_session_metadata(request: Request) -> SessionMetadata:
    return SessionMetadata(
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignUpRequest,
    http_request: Request,
    response: Response,
    dependencies: SignUpDependencies = Depends(get_signup_dependencies),
    refresh_service: RefreshSessionService = Depends(get_refresh_service),
) -> TokenResponse:
    try:
        command = await dependencies.command_factory.create(request)
        result = await dependencies.use_case.execute(command)
    except (EmailAlreadyExistsError, IntegrityError) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already exists",
        ) from error

    token_pair = await refresh_service.create(result.user, get_session_metadata(http_request))
    set_refresh_cookie(response, token_pair.refresh_token)
    return TokenResponse(
        access_token=token_pair.access_token,
        user=UserResponse(
            id=str(result.user.id),
            email=result.user.email.value,
            display_name=result.user.display_name.value,
        ),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    service: RefreshSessionService = Depends(get_refresh_service),
) -> TokenResponse:
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid refresh token",
        )
    try:
        result = await service.rotate(refresh_token, get_session_metadata(request))
    except InvalidRefreshSessionError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid refresh token",
        ) from error

    set_refresh_cookie(response, result.refresh_token)
    return TokenResponse(
        access_token=result.access_token,
        user=UserResponse(
            id=str(result.user.id),
            email=result.user.email.value,
            display_name=result.user.display_name.value,
        ),
    )

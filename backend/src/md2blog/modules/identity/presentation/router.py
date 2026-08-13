from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from md2blog.modules.identity.application.port.inbound.login import LoginRequest, LoginUseCase
from md2blog.modules.identity.application.port.inbound.models import TokenResponse, UserResponse
from md2blog.modules.identity.application.port.inbound.signup import SignUpRequest
from md2blog.modules.identity.application.service.logout import LogoutSessionService
from md2blog.modules.identity.application.service.refresh import (
    RefreshSessionService,
    SessionMetadata,
)
from md2blog.modules.identity.application.service.signup import EmailAlreadyExistsError
from md2blog.modules.identity.domain.auth_session import (
    InvalidRefreshSessionError,
    RefreshTokenReuseDetectedError,
)
from md2blog.modules.identity.domain.commands import LoginCommand
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import Email, RawPassword
from md2blog.modules.identity.presentation.dependencies import (
    SignUpDependencies,
    get_current_user,
    get_login_use_case,
    get_logout_service,
    get_refresh_service,
    get_signup_dependencies,
)
from md2blog.settings import Settings, get_settings
from md2blog.shared.presentation.errors import ErrorCode
from md2blog.shared.presentation.exception_handlers import error_response

router = APIRouter(prefix="/auth", tags=["auth"])
REFRESH_TOKEN_COOKIE = "refresh_token"


def set_refresh_cookie(response: Response, refresh_token: str, settings: Settings) -> None:
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=settings.refresh_token_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.refresh_token_cookie_secure,
        samesite=settings.refresh_token_cookie_samesite,
        path="/auth",
    )


def delete_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        secure=settings.refresh_token_cookie_secure,
        httponly=True,
        samesite=settings.refresh_token_cookie_samesite,
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
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    command = await dependencies.command_factory.create(request)
    try:
        result = await dependencies.use_case.execute(command)
    except IntegrityError as error:
        raise EmailAlreadyExistsError from error

    token_pair = await refresh_service.create(result.user, get_session_metadata(http_request))
    set_refresh_cookie(response, token_pair.refresh_token, settings)
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
    settings: Settings = Depends(get_settings),
) -> TokenResponse | JSONResponse:
    if refresh_token is None:
        raise InvalidRefreshSessionError
    try:
        result = await service.rotate(refresh_token, get_session_metadata(request))
    except RefreshTokenReuseDetectedError:
        rejection = error_response(
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.AUTH_INVALID_REFRESH_TOKEN,
            "유효하지 않은 리프레시 토큰입니다.",
        )
        delete_refresh_cookie(rejection, settings)
        return rejection

    set_refresh_cookie(response, result.refresh_token, settings)
    return TokenResponse(
        access_token=result.access_token,
        user=UserResponse(
            id=str(result.user.id),
            email=result.user.email.value,
            display_name=result.user.display_name.value,
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    response: Response,
    use_case: LoginUseCase = Depends(get_login_use_case),
    refresh_service: RefreshSessionService = Depends(get_refresh_service),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    result = await use_case.execute(
        LoginCommand(
            email=Email(str(request.email)),
            password=RawPassword(request.password),
        )
    )

    token_pair = await refresh_service.create(result.user, get_session_metadata(http_request))
    set_refresh_cookie(response, token_pair.refresh_token, settings)
    return TokenResponse(
        access_token=token_pair.access_token,
        user=UserResponse(
            id=str(result.user.id),
            email=result.user.email.value,
            display_name=result.user.display_name.value,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email.value,
        display_name=current_user.display_name.value,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    service: LogoutSessionService = Depends(get_logout_service),
    settings: Settings = Depends(get_settings),
) -> None:
    await service.logout(refresh_token)
    delete_refresh_cookie(response, settings)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    response: Response,
    current_user: User = Depends(get_current_user),
    service: LogoutSessionService = Depends(get_logout_service),
    settings: Settings = Depends(get_settings),
) -> None:
    await service.logout_all(current_user.id)
    delete_refresh_cookie(response, settings)

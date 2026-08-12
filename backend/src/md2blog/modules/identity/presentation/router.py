from datetime import timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.identity.application.factory.signup import SignUpCommandFactory
from md2blog.modules.identity.application.port.inbound.models import TokenResponse, UserResponse
from md2blog.modules.identity.application.port.inbound.signup import SignUpRequest, SignUpUseCase
from md2blog.modules.identity.application.service.refresh import (
    RefreshSessionService,
    SessionMetadata,
)
from md2blog.modules.identity.application.service.signup import EmailAlreadyExistsError, SignUp
from md2blog.modules.identity.domain.auth_session import InvalidRefreshSessionError
from md2blog.modules.identity.infrastructure.passwords import Argon2PasswordHasher
from md2blog.modules.identity.infrastructure.repositories import SqlAlchemyUserRepository
from md2blog.modules.identity.infrastructure.session_repositories import (
    SqlAlchemyAuthSessionRepository,
)
from md2blog.modules.identity.infrastructure.tokens import (
    JwtAccessTokenIssuer,
    SecureRefreshTokenManager,
    SystemClock,
)
from md2blog.settings import get_settings
from md2blog.shared.infrastructure.database import get_session

router = APIRouter(prefix="/auth", tags=["auth"])
REFRESH_TOKEN_COOKIE = "refresh_token"


def get_signup_dependencies(
    session: AsyncSession = Depends(get_session),
) -> tuple[SignUpCommandFactory, SignUpUseCase]:
    settings = get_settings()
    users = SqlAlchemyUserRepository(session)
    return (
        SignUpCommandFactory(users=users, password_hasher=Argon2PasswordHasher()),
        SignUp(
            users=users,
            token_issuer=JwtAccessTokenIssuer(
            settings.jwt_secret_key.get_secret_value(),
            timedelta(minutes=settings.access_token_ttl_minutes),
        ),
        ),
    )


def get_refresh_service(
    session: AsyncSession = Depends(get_session),
) -> RefreshSessionService:
    settings = get_settings()
    return RefreshSessionService(
        sessions=SqlAlchemyAuthSessionRepository(session),
        users=SqlAlchemyUserRepository(session),
        refresh_tokens=SecureRefreshTokenManager(),
        access_tokens=JwtAccessTokenIssuer(
            settings.jwt_secret_key.get_secret_value(),
            timedelta(minutes=settings.access_token_ttl_minutes),
        ),
        clock=SystemClock(),
        refresh_ttl=timedelta(days=settings.refresh_token_ttl_days),
    )


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
    dependencies: tuple[SignUpCommandFactory, SignUpUseCase] = Depends(get_signup_dependencies),
    refresh_service: RefreshSessionService = Depends(get_refresh_service),
) -> TokenResponse:
    command_factory, use_case = dependencies
    try:
        command = await command_factory.create(request)
        result = await use_case.execute(command)
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

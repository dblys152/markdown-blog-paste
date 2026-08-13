from dataclasses import dataclass
from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.identity.application.factory.signup import SignUpCommandFactory
from md2blog.modules.identity.application.port.inbound.login import LoginUseCase
from md2blog.modules.identity.application.port.inbound.signup import SignUpUseCase
from md2blog.modules.identity.application.port.outbound.security import InvalidAccessTokenError
from md2blog.modules.identity.application.service.authenticate_access_token import (
    AuthenticateAccessToken,
    AuthenticationRequiredError,
)
from md2blog.modules.identity.application.service.login import Login
from md2blog.modules.identity.application.service.refresh import RefreshSessionService
from md2blog.modules.identity.application.service.signup import SignUp
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.infrastructure.passwords import Argon2PasswordHasher
from md2blog.modules.identity.infrastructure.repositories import SqlAlchemyUserRepository
from md2blog.modules.identity.infrastructure.session_repositories import (
    SqlAlchemyAuthSessionRepository,
)
from md2blog.modules.identity.infrastructure.tokens import (
    JwtAccessTokenDecoder,
    JwtAccessTokenIssuer,
    SecureRefreshTokenManager,
    SystemClock,
)
from md2blog.settings import get_settings
from md2blog.shared.infrastructure.database import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@dataclass(frozen=True, slots=True)
class SignUpDependencies:
    command_factory: SignUpCommandFactory
    use_case: SignUpUseCase


def get_authenticate_access_token(
    session: AsyncSession = Depends(get_session),
) -> AuthenticateAccessToken:
    settings = get_settings()
    return AuthenticateAccessToken(
        decoder=JwtAccessTokenDecoder(settings.jwt_secret_key.get_secret_value()),
        users=SqlAlchemyUserRepository(session),
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: AuthenticateAccessToken = Depends(get_authenticate_access_token),
) -> User:
    try:
        return await service.execute(token)
    except (InvalidAccessTokenError, AuthenticationRequiredError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def get_login_use_case(
    session: AsyncSession = Depends(get_session),
) -> LoginUseCase:
    return Login(
        users=SqlAlchemyUserRepository(session),
        password_hasher=Argon2PasswordHasher(),
    )


def get_signup_dependencies(
    session: AsyncSession = Depends(get_session),
) -> SignUpDependencies:
    settings = get_settings()
    users = SqlAlchemyUserRepository(session)
    return SignUpDependencies(
        command_factory=SignUpCommandFactory(
            users=users,
            password_hasher=Argon2PasswordHasher(),
        ),
        use_case=SignUp(
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

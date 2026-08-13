from dataclasses import dataclass
from datetime import timedelta

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.identity.application.factory.signup import SignUpCommandFactory
from md2blog.modules.identity.application.port.inbound.login import LoginUseCase
from md2blog.modules.identity.application.port.inbound.signup import SignUpUseCase
from md2blog.modules.identity.application.service.login import Login
from md2blog.modules.identity.application.service.refresh import RefreshSessionService
from md2blog.modules.identity.application.service.signup import SignUp
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


@dataclass(frozen=True, slots=True)
class SignUpDependencies:
    command_factory: SignUpCommandFactory
    use_case: SignUpUseCase


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

from dataclasses import dataclass
from datetime import timedelta

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.identity.application.factory.signup import SignUpCommandFactory
from md2blog.modules.identity.application.port.inbound.account import DeleteAccountUseCase
from md2blog.modules.identity.application.port.inbound.email_verification import (
    ConfirmEmailVerificationUseCase,
    IssueEmailVerificationUseCase,
)
from md2blog.modules.identity.application.port.inbound.login import LoginUseCase
from md2blog.modules.identity.application.port.inbound.password_reset import (
    ConfirmPasswordResetUseCase,
    RequestPasswordResetUseCase,
)
from md2blog.modules.identity.application.port.inbound.signup import SignUpUseCase
from md2blog.modules.identity.application.port.outbound.email import EmailDeliveryError, EmailSender
from md2blog.modules.identity.application.port.outbound.security import InvalidAccessTokenError
from md2blog.modules.identity.application.service.authenticate_access_token import (
    AuthenticateAccessToken,
    AuthenticationRequiredError,
)
from md2blog.modules.identity.application.service.delete_account import DeleteAccount
from md2blog.modules.identity.application.service.email_verification import (
    ConfirmEmailVerification,
    EmailVerificationPolicy,
    IssueEmailVerification,
)
from md2blog.modules.identity.application.service.login import Login
from md2blog.modules.identity.application.service.logout import LogoutSessionService
from md2blog.modules.identity.application.service.password_reset import (
    ConfirmPasswordReset,
    PasswordResetPolicy,
    RequestPasswordReset,
)
from md2blog.modules.identity.application.service.refresh import RefreshSessionService
from md2blog.modules.identity.application.service.signup import SignUp
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.infrastructure.email import GmailSmtpEmailSender
from md2blog.modules.identity.infrastructure.email_verification_repositories import (
    SqlAlchemyEmailVerificationTokenRepository,
)
from md2blog.modules.identity.infrastructure.password_reset_repositories import (
    SqlAlchemyPasswordResetTokenRepository,
)
from md2blog.modules.identity.infrastructure.passwords import Argon2PasswordHasher
from md2blog.modules.identity.infrastructure.repositories import SqlAlchemyUserRepository
from md2blog.modules.identity.infrastructure.session_repositories import (
    SqlAlchemyAuthSessionRepository,
)
from md2blog.modules.identity.infrastructure.tokens import (
    JwtAccessTokenDecoder,
    JwtAccessTokenIssuer,
    SecureEmailVerificationTokenManager,
    SecurePasswordResetTokenManager,
    SecureRefreshTokenManager,
    SystemClock,
)
from md2blog.settings import Settings, get_settings
from md2blog.shared.infrastructure.database import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


@dataclass(frozen=True, slots=True)
class SignUpDependencies:
    command_factory: SignUpCommandFactory
    use_case: SignUpUseCase


def get_email_sender(settings: Settings = Depends(get_settings)) -> EmailSender:
    if (
        settings.smtp_username is None
        or settings.smtp_password is None
        or settings.email_from is None
    ):
        raise EmailDeliveryError("SMTP configuration is incomplete")
    return GmailSmtpEmailSender(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password.get_secret_value(),
        from_address=settings.email_from,
    )


def get_issue_email_verification(
    session: AsyncSession = Depends(get_session),
    email_sender: EmailSender = Depends(get_email_sender),
    settings: Settings = Depends(get_settings),
) -> IssueEmailVerificationUseCase:
    return IssueEmailVerification(
        tokens=SqlAlchemyEmailVerificationTokenRepository(session),
        token_manager=SecureEmailVerificationTokenManager(),
        email_sender=email_sender,
        clock=SystemClock(),
        policy=EmailVerificationPolicy(
            token_ttl=timedelta(hours=settings.email_verification_token_ttl_hours),
            resend_cooldown=timedelta(
                seconds=settings.email_verification_resend_cooldown_seconds
            ),
            daily_limit=settings.email_verification_daily_limit,
        ),
        frontend_url=settings.frontend_url,
    )


def get_confirm_email_verification(
    session: AsyncSession = Depends(get_session),
) -> ConfirmEmailVerificationUseCase:
    return ConfirmEmailVerification(
        users=SqlAlchemyUserRepository(session),
        tokens=SqlAlchemyEmailVerificationTokenRepository(session),
        token_manager=SecureEmailVerificationTokenManager(),
        clock=SystemClock(),
    )


def get_authenticate_access_token(
    session: AsyncSession = Depends(get_session),
) -> AuthenticateAccessToken:
    settings = get_settings()
    return AuthenticateAccessToken(
        decoder=JwtAccessTokenDecoder(settings.jwt_secret_key.get_secret_value()),
        users=SqlAlchemyUserRepository(session),
    )


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    service: AuthenticateAccessToken = Depends(get_authenticate_access_token),
) -> User:
    if token is None:
        raise AuthenticationRequiredError
    try:
        return await service.execute(token)
    except (InvalidAccessTokenError, AuthenticationRequiredError) as error:
        raise AuthenticationRequiredError from error


async def get_email_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    current_user.ensure_email_verified()
    return current_user


def get_login_use_case(
    session: AsyncSession = Depends(get_session),
) -> LoginUseCase:
    return Login(
        users=SqlAlchemyUserRepository(session),
        password_hasher=Argon2PasswordHasher(),
    )


def get_delete_account(
    session: AsyncSession = Depends(get_session),
) -> DeleteAccountUseCase:
    return DeleteAccount(
        users=SqlAlchemyUserRepository(session),
        password_hasher=Argon2PasswordHasher(),
    )


def get_request_password_reset(
    session: AsyncSession = Depends(get_session),
    email_sender: EmailSender = Depends(get_email_sender),
    settings: Settings = Depends(get_settings),
) -> RequestPasswordResetUseCase:
    return RequestPasswordReset(
        users=SqlAlchemyUserRepository(session),
        tokens=SqlAlchemyPasswordResetTokenRepository(session),
        token_manager=SecurePasswordResetTokenManager(),
        email_sender=email_sender,
        clock=SystemClock(),
        policy=PasswordResetPolicy(
            token_ttl=timedelta(minutes=settings.password_reset_token_ttl_minutes),
            resend_cooldown=timedelta(
                seconds=settings.password_reset_resend_cooldown_seconds
            ),
            daily_limit=settings.password_reset_daily_limit,
        ),
        frontend_url=settings.frontend_url,
    )


def get_confirm_password_reset(
    session: AsyncSession = Depends(get_session),
) -> ConfirmPasswordResetUseCase:
    return ConfirmPasswordReset(
        users=SqlAlchemyUserRepository(session),
        sessions=SqlAlchemyAuthSessionRepository(session),
        tokens=SqlAlchemyPasswordResetTokenRepository(session),
        token_manager=SecurePasswordResetTokenManager(),
        password_hasher=Argon2PasswordHasher(),
        clock=SystemClock(),
    )


def get_signup_dependencies(
    session: AsyncSession = Depends(get_session),
    email_verification: IssueEmailVerificationUseCase = Depends(get_issue_email_verification),
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
            email_verification=email_verification,
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


def get_logout_service(
    session: AsyncSession = Depends(get_session),
) -> LogoutSessionService:
    return LogoutSessionService(
        sessions=SqlAlchemyAuthSessionRepository(session),
        refresh_tokens=SecureRefreshTokenManager(),
        clock=SystemClock(),
    )

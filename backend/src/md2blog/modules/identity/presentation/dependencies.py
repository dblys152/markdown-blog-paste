from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from md2blog.modules.identity.application.event_handlers import (
    EmailVerificationRequestedHandler,
    PasswordResetRequestedHandler,
    SecurityAuditLogHandler,
)
from md2blog.modules.identity.application.factory.signup import SignUpCommandFactory
from md2blog.modules.identity.application.port.inbound.account import DeleteAccountUseCase
from md2blog.modules.identity.application.port.inbound.email_verification import (
    ConfirmEmailVerificationUseCase,
    IssueEmailVerificationUseCase,
)
from md2blog.modules.identity.application.port.inbound.google_auth import (
    ConnectGoogleUseCase,
    DisconnectGoogleUseCase,
    GetGoogleConnectionUseCase,
    GoogleLoginUseCase,
    GoogleSignUpUseCase,
    LinkGoogleAndLoginUseCase,
)
from md2blog.modules.identity.application.port.inbound.login import LoginUseCase
from md2blog.modules.identity.application.port.inbound.password_reset import (
    ConfirmPasswordResetUseCase,
    RequestPasswordResetUseCase,
)
from md2blog.modules.identity.application.port.inbound.profile import (
    UpdateDisplayNameUseCase,
)
from md2blog.modules.identity.application.port.inbound.signup import SignUpUseCase
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
from md2blog.modules.identity.application.service.google_auth import (
    ConnectGoogle,
    DisconnectGoogle,
    GetGoogleConnection,
    GoogleLogin,
    GoogleSignUp,
    LinkGoogleAndLogin,
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
from md2blog.modules.identity.application.service.update_display_name import UpdateDisplayName
from md2blog.modules.identity.domain.account_confirmation_token import (
    AccountConfirmationTokenPurpose,
)
from md2blog.modules.identity.domain.events import (
    AccountDeleted,
    AllSessionsRevoked,
    AuthenticationFailed,
    AuthenticationSucceeded,
    EmailVerificationRequested,
    EmailVerified,
    PasswordResetCompleted,
    PasswordResetRequested,
    UserIdentityLinked,
    UserIdentityUnlinked,
)
from md2blog.modules.identity.domain.google_identity_policy import (
    GoogleIdentityLinkPolicy,
    GoogleIdentityUnlinkPolicy,
)
from md2blog.modules.identity.domain.login_failure_state import LoginFailurePolicy
from md2blog.modules.identity.domain.nickname_policy import NicknameUniquenessPolicy
from md2blog.modules.identity.domain.token_policy import ACCESS_TOKEN_TTL, REFRESH_TOKEN_TTL
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.infrastructure.account_confirmation_token_repositories import (
    SqlAlchemyAccountConfirmationTokenRepository,
)
from md2blog.modules.identity.infrastructure.google_identity import GoogleIdTokenVerifier
from md2blog.modules.identity.infrastructure.login_failure_states import (
    SqlAlchemyLoginFailureStateRepository,
)
from md2blog.modules.identity.infrastructure.passwords import Argon2PasswordHasher
from md2blog.modules.identity.infrastructure.repositories import SqlAlchemyUserRepository
from md2blog.modules.identity.infrastructure.session_repositories import (
    SqlAlchemyAuthSessionRepository,
)
from md2blog.modules.identity.infrastructure.tokens import (
    JwtAccessTokenDecoder,
    JwtAccessTokenIssuer,
    SecureAccountConfirmationTokenManager,
    SecureRefreshTokenManager,
    SystemClock,
)
from md2blog.modules.identity.infrastructure.user_identity_repositories import (
    SqlAlchemyUserIdentityRepository,
)
from md2blog.settings import Settings, get_settings
from md2blog.shared.application.events import DomainEventPublisher
from md2blog.shared.infrastructure.database import get_session
from md2blog.shared.infrastructure.event_repositories import (
    SqlAlchemyOutboxMessageRepository,
    SqlAlchemySecurityAuditLogRepository,
)
from md2blog.shared.infrastructure.sensitive_value_cipher import (
    FernetSensitiveValueCipher,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


@dataclass(frozen=True, slots=True)
class SignUpDependencies:
    command_factory: SignUpCommandFactory
    use_case: SignUpUseCase


def get_domain_event_publisher(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> DomainEventPublisher:
    publisher = DomainEventPublisher()
    outbox = SqlAlchemyOutboxMessageRepository(session)
    cipher = FernetSensitiveValueCipher(settings.outbox_token_encryption_key.get_secret_value())
    publisher.subscribe(
        EmailVerificationRequested,
        EmailVerificationRequestedHandler(outbox, cipher, settings.frontend_url).handle,
    )
    publisher.subscribe(
        PasswordResetRequested,
        PasswordResetRequestedHandler(outbox, cipher, settings.frontend_url).handle,
    )
    audit_handler = SecurityAuditLogHandler(SqlAlchemySecurityAuditLogRepository(session))
    publisher.subscribe(AuthenticationSucceeded, audit_handler.handle)
    publisher.subscribe(AuthenticationFailed, audit_handler.handle)
    publisher.subscribe(EmailVerified, audit_handler.handle)
    publisher.subscribe(PasswordResetCompleted, audit_handler.handle)
    publisher.subscribe(AllSessionsRevoked, audit_handler.handle)
    publisher.subscribe(UserIdentityLinked, audit_handler.handle)
    publisher.subscribe(UserIdentityUnlinked, audit_handler.handle)
    publisher.subscribe(AccountDeleted, audit_handler.handle)
    return publisher


def get_issue_email_verification(
    session: AsyncSession = Depends(get_session),
    events: DomainEventPublisher = Depends(get_domain_event_publisher),
) -> IssueEmailVerificationUseCase:
    return IssueEmailVerification(
        tokens=SqlAlchemyAccountConfirmationTokenRepository(
            session, AccountConfirmationTokenPurpose.EMAIL_VERIFICATION
        ),
        token_manager=SecureAccountConfirmationTokenManager(),
        events=events,
        clock=SystemClock(),
        policy=EmailVerificationPolicy(),
    )


def get_confirm_email_verification(
    session: AsyncSession = Depends(get_session),
    events: DomainEventPublisher = Depends(get_domain_event_publisher),
) -> ConfirmEmailVerificationUseCase:
    return ConfirmEmailVerification(
        users=SqlAlchemyUserRepository(session),
        tokens=SqlAlchemyAccountConfirmationTokenRepository(
            session, AccountConfirmationTokenPurpose.EMAIL_VERIFICATION
        ),
        token_manager=SecureAccountConfirmationTokenManager(),
        events=events,
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
    events: DomainEventPublisher = Depends(get_domain_event_publisher),
) -> LoginUseCase:
    return Login(
        users=SqlAlchemyUserRepository(session),
        password_hasher=Argon2PasswordHasher(),
        failures=SqlAlchemyLoginFailureStateRepository(session),
        clock=SystemClock(),
        policy=LoginFailurePolicy(),
        events=events,
    )


def get_google_verifier(settings: Settings = Depends(get_settings)) -> GoogleIdTokenVerifier:
    if settings.google_client_id is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google 로그인이 설정되지 않았습니다.",
        )
    return GoogleIdTokenVerifier(settings.google_client_id)


def get_google_login(
    session: AsyncSession = Depends(get_session),
    verifier: GoogleIdTokenVerifier = Depends(get_google_verifier),
) -> GoogleLoginUseCase:
    return GoogleLogin(
        SqlAlchemyUserRepository(session),
        SqlAlchemyUserIdentityRepository(session),
        verifier,
    )


def get_google_signup(
    session: AsyncSession = Depends(get_session),
    verifier: GoogleIdTokenVerifier = Depends(get_google_verifier),
    events: DomainEventPublisher = Depends(get_domain_event_publisher),
) -> GoogleSignUpUseCase:
    return GoogleSignUp(
        SqlAlchemyUserRepository(session),
        SqlAlchemyUserIdentityRepository(session),
        verifier,
        NicknameUniquenessPolicy(),
        SystemClock(),
        events,
    )


def get_link_google_and_login(
    session: AsyncSession = Depends(get_session),
    verifier: GoogleIdTokenVerifier = Depends(get_google_verifier),
    events: DomainEventPublisher = Depends(get_domain_event_publisher),
) -> LinkGoogleAndLoginUseCase:
    return LinkGoogleAndLogin(
        SqlAlchemyUserRepository(session),
        SqlAlchemyUserIdentityRepository(session),
        verifier,
        Argon2PasswordHasher(),
        SystemClock(),
        events,
    )


def get_connect_google(
    session: AsyncSession = Depends(get_session),
    verifier: GoogleIdTokenVerifier = Depends(get_google_verifier),
    events: DomainEventPublisher = Depends(get_domain_event_publisher),
) -> ConnectGoogleUseCase:
    return ConnectGoogle(
        SqlAlchemyUserIdentityRepository(session),
        verifier,
        SystemClock(),
        GoogleIdentityLinkPolicy(),
        events,
    )


def get_disconnect_google(
    session: AsyncSession = Depends(get_session),
    events: DomainEventPublisher = Depends(get_domain_event_publisher),
) -> DisconnectGoogleUseCase:
    return DisconnectGoogle(
        SqlAlchemyUserIdentityRepository(session),
        GoogleIdentityUnlinkPolicy(),
        events,
        SystemClock(),
    )


def get_google_connection(
    session: AsyncSession = Depends(get_session),
) -> GetGoogleConnectionUseCase:
    return GetGoogleConnection(SqlAlchemyUserIdentityRepository(session))


def get_delete_account(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    events: DomainEventPublisher = Depends(get_domain_event_publisher),
) -> DeleteAccountUseCase:
    return DeleteAccount(
        users=SqlAlchemyUserRepository(session),
        password_hasher=Argon2PasswordHasher(),
        identities=SqlAlchemyUserIdentityRepository(session),
        google_verifier=(
            GoogleIdTokenVerifier(settings.google_client_id) if settings.google_client_id else None
        ),
        events=events,
        clock=SystemClock(),
    )


def get_update_display_name(
    session: AsyncSession = Depends(get_session),
) -> UpdateDisplayNameUseCase:
    return UpdateDisplayName(
        users=SqlAlchemyUserRepository(session),
        nickname_policy=NicknameUniquenessPolicy(),
        clock=SystemClock(),
    )


def get_request_password_reset(
    session: AsyncSession = Depends(get_session),
    events: DomainEventPublisher = Depends(get_domain_event_publisher),
) -> RequestPasswordResetUseCase:
    return RequestPasswordReset(
        users=SqlAlchemyUserRepository(session),
        tokens=SqlAlchemyAccountConfirmationTokenRepository(
            session, AccountConfirmationTokenPurpose.PASSWORD_RESET
        ),
        token_manager=SecureAccountConfirmationTokenManager(),
        events=events,
        clock=SystemClock(),
        policy=PasswordResetPolicy(),
    )


def get_confirm_password_reset(
    session: AsyncSession = Depends(get_session),
    events: DomainEventPublisher = Depends(get_domain_event_publisher),
) -> ConfirmPasswordResetUseCase:
    return ConfirmPasswordReset(
        users=SqlAlchemyUserRepository(session),
        sessions=SqlAlchemyAuthSessionRepository(session),
        tokens=SqlAlchemyAccountConfirmationTokenRepository(
            session, AccountConfirmationTokenPurpose.PASSWORD_RESET
        ),
        token_manager=SecureAccountConfirmationTokenManager(),
        password_hasher=Argon2PasswordHasher(),
        events=events,
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
                ACCESS_TOKEN_TTL,
            ),
            email_verification=email_verification,
            nickname_policy=NicknameUniquenessPolicy(),
            clock=SystemClock(),
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
            ACCESS_TOKEN_TTL,
        ),
        clock=SystemClock(),
        refresh_ttl=REFRESH_TOKEN_TTL,
    )


def get_logout_service(
    session: AsyncSession = Depends(get_session),
    events: DomainEventPublisher = Depends(get_domain_event_publisher),
) -> LogoutSessionService:
    return LogoutSessionService(
        sessions=SqlAlchemyAuthSessionRepository(session),
        refresh_tokens=SecureRefreshTokenManager(),
        clock=SystemClock(),
        events=events,
    )

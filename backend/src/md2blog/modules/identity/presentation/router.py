from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from md2blog.modules.identity.application.models.google_auth import GoogleLoginStatus
from md2blog.modules.identity.application.port.inbound.account import (
    DeleteAccountRequest,
    DeleteAccountUseCase,
)
from md2blog.modules.identity.application.port.inbound.email_verification import (
    ConfirmEmailVerificationUseCase,
    IssueEmailVerificationUseCase,
)
from md2blog.modules.identity.application.port.inbound.google_auth import (
    ConnectGoogleUseCase,
    DisconnectGoogleUseCase,
    GetGoogleConnectionUseCase,
    GoogleConnectionResponse,
    GoogleCredentialRequest,
    GoogleLoginFlowResponse,
    GoogleLoginUseCase,
    GoogleSignUpRequest,
    GoogleSignUpUseCase,
    LinkGoogleAndLoginRequest,
    LinkGoogleAndLoginUseCase,
)
from md2blog.modules.identity.application.port.inbound.login import LoginRequest, LoginUseCase
from md2blog.modules.identity.application.port.inbound.models import (
    EmailVerificationConfirmRequest,
    TokenResponse,
    UserResponse,
)
from md2blog.modules.identity.application.port.inbound.password_reset import (
    ConfirmPasswordResetUseCase,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RequestPasswordResetUseCase,
)
from md2blog.modules.identity.application.port.inbound.profile import (
    UpdateDisplayNameRequest,
    UpdateDisplayNameUseCase,
)
from md2blog.modules.identity.application.port.inbound.signup import SignUpRequest
from md2blog.modules.identity.application.service.logout import LogoutSessionService
from md2blog.modules.identity.application.service.refresh import (
    RefreshSessionService,
    SessionMetadata,
)
from md2blog.modules.identity.application.service.signup import (
    EmailAlreadyExistsError,
)
from md2blog.modules.identity.domain.auth_session import (
    InvalidRefreshSessionError,
    RefreshTokenReuseDetectedError,
)
from md2blog.modules.identity.domain.commands import (
    ConfirmPasswordResetCommand,
    DeleteAccountCommand,
    GoogleSignUpCommand,
    LinkGoogleAndLoginCommand,
    LoginCommand,
    RequestPasswordResetCommand,
    UpdateDisplayNameCommand,
)
from md2blog.modules.identity.domain.nickname_policy import NicknameAlreadyInUseError
from md2blog.modules.identity.domain.user import User
from md2blog.modules.identity.domain.value_objects import DisplayName, Email, RawPassword
from md2blog.modules.identity.presentation.dependencies import (
    SignUpDependencies,
    get_confirm_email_verification,
    get_confirm_password_reset,
    get_connect_google,
    get_current_user,
    get_delete_account,
    get_disconnect_google,
    get_google_connection,
    get_google_login,
    get_google_signup,
    get_issue_email_verification,
    get_link_google_and_login,
    get_login_use_case,
    get_logout_service,
    get_refresh_service,
    get_request_password_reset,
    get_signup_dependencies,
    get_update_display_name,
)
from md2blog.settings import Settings, get_settings
from md2blog.shared.presentation.errors import ErrorCode
from md2blog.shared.presentation.exception_handlers import error_response

router = APIRouter(prefix="/auth", tags=["auth"])
REFRESH_TOKEN_COOKIE = "refresh_token"


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email.value,
        display_name=user.display_name.value,
        email_verified=user.is_email_verified,
    )


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
        if "uq_users_display_name_lower" in str(error.orig):
            raise NicknameAlreadyInUseError from error
        raise EmailAlreadyExistsError from error

    token_pair = await refresh_service.create(result.user, get_session_metadata(http_request))
    set_refresh_cookie(response, token_pair.refresh_token, settings)
    return TokenResponse(
        access_token=token_pair.access_token,
        user=to_user_response(result.user),
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
        user=to_user_response(result.user),
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
        user=to_user_response(result.user),
    )


@router.post("/google/login", response_model=TokenResponse | GoogleLoginFlowResponse)
async def google_login(
    request: GoogleCredentialRequest,
    http_request: Request,
    response: Response,
    use_case: GoogleLoginUseCase = Depends(get_google_login),
    refresh_service: RefreshSessionService = Depends(get_refresh_service),
    settings: Settings = Depends(get_settings),
) -> TokenResponse | GoogleLoginFlowResponse:
    result = await use_case.execute(request.credential)
    if result.status is not GoogleLoginStatus.AUTHENTICATED or result.user is None:
        if result.status is GoogleLoginStatus.LINK_REQUIRED:
            return GoogleLoginFlowResponse(
                status="link_required",
                email=result.email.value,
            )
        return GoogleLoginFlowResponse(
            status="signup_required",
            email=result.email.value,
        )
    token_pair = await refresh_service.create(result.user, get_session_metadata(http_request))
    set_refresh_cookie(response, token_pair.refresh_token, settings)
    return TokenResponse(access_token=token_pair.access_token, user=to_user_response(result.user))


@router.post("/google/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def google_signup(
    request: GoogleSignUpRequest,
    http_request: Request,
    response: Response,
    use_case: GoogleSignUpUseCase = Depends(get_google_signup),
    refresh_service: RefreshSessionService = Depends(get_refresh_service),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    user = await use_case.execute(
        GoogleSignUpCommand(
            credential=request.credential,
            display_name=DisplayName(request.display_name),
        )
    )
    token_pair = await refresh_service.create(user, get_session_metadata(http_request))
    set_refresh_cookie(response, token_pair.refresh_token, settings)
    return TokenResponse(access_token=token_pair.access_token, user=to_user_response(user))


@router.post("/google/link-and-login", response_model=TokenResponse)
async def google_link_and_login(
    request: LinkGoogleAndLoginRequest,
    http_request: Request,
    response: Response,
    use_case: LinkGoogleAndLoginUseCase = Depends(get_link_google_and_login),
    refresh_service: RefreshSessionService = Depends(get_refresh_service),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    user = await use_case.execute(
        LinkGoogleAndLoginCommand(
            credential=request.credential,
            password=RawPassword(request.password),
        )
    )
    token_pair = await refresh_service.create(user, get_session_metadata(http_request))
    set_refresh_cookie(response, token_pair.refresh_token, settings)
    return TokenResponse(access_token=token_pair.access_token, user=to_user_response(user))


@router.get("/google/connection", response_model=GoogleConnectionResponse)
async def google_connection(
    current_user: User = Depends(get_current_user),
    use_case: GetGoogleConnectionUseCase = Depends(get_google_connection),
) -> GoogleConnectionResponse:
    connection = await use_case.execute(current_user)
    return GoogleConnectionResponse(
        connected=connection.connected,
        email=connection.email,
        can_disconnect=connection.can_disconnect,
    )


@router.post("/google/connection", status_code=status.HTTP_204_NO_CONTENT)
async def connect_google(
    request: GoogleCredentialRequest,
    current_user: User = Depends(get_current_user),
    use_case: ConnectGoogleUseCase = Depends(get_connect_google),
) -> None:
    await use_case.execute(current_user, request.credential)


@router.delete("/google/connection", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_google(
    current_user: User = Depends(get_current_user),
    use_case: DisconnectGoogleUseCase = Depends(get_disconnect_google),
) -> None:
    await use_case.execute(current_user)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return to_user_response(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    request: UpdateDisplayNameRequest,
    current_user: User = Depends(get_current_user),
    use_case: UpdateDisplayNameUseCase = Depends(get_update_display_name),
) -> UserResponse:
    try:
        user = await use_case.execute(
            current_user,
            UpdateDisplayNameCommand(display_name=DisplayName(request.display_name)),
        )
    except IntegrityError as error:
        raise NicknameAlreadyInUseError from error
    return to_user_response(user)


@router.post("/email-verification/request", status_code=status.HTTP_204_NO_CONTENT)
async def request_email_verification(
    current_user: User = Depends(get_current_user),
    use_case: IssueEmailVerificationUseCase = Depends(get_issue_email_verification),
) -> None:
    await use_case.execute(current_user)


@router.post("/email-verification/confirm", response_model=UserResponse)
async def confirm_email_verification(
    request: EmailVerificationConfirmRequest,
    use_case: ConfirmEmailVerificationUseCase = Depends(get_confirm_email_verification),
) -> UserResponse:
    return to_user_response(await use_case.execute(request.token))


@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
async def request_password_reset(
    request: PasswordResetRequest,
    use_case: RequestPasswordResetUseCase = Depends(get_request_password_reset),
) -> None:
    await use_case.execute(RequestPasswordResetCommand(email=Email(str(request.email))))


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    response: Response,
    use_case: ConfirmPasswordResetUseCase = Depends(get_confirm_password_reset),
    settings: Settings = Depends(get_settings),
) -> None:
    await use_case.execute(
        ConfirmPasswordResetCommand(
            token=request.token,
            new_password=RawPassword(request.new_password),
        )
    )
    delete_refresh_cookie(response, settings)


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


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    request: DeleteAccountRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    use_case: DeleteAccountUseCase = Depends(get_delete_account),
    settings: Settings = Depends(get_settings),
) -> None:
    await use_case.execute(
        current_user,
        DeleteAccountCommand(
            password=RawPassword(request.password) if request.password else None,
            google_credential=request.google_credential,
        ),
    )
    delete_refresh_cookie(response, settings)

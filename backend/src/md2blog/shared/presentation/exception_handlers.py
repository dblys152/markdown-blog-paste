from collections.abc import Mapping

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from md2blog.modules.identity.application.port.outbound.security import InvalidAccessTokenError
from md2blog.modules.identity.application.service.authenticate_access_token import (
    AuthenticationRequiredError,
)
from md2blog.modules.identity.application.service.signup import EmailAlreadyExistsError
from md2blog.modules.identity.domain.auth_session import InvalidRefreshSessionError
from md2blog.modules.identity.domain.user import AuthenticationFailedError
from md2blog.modules.workspace.domain.page import (
    InvalidPageMoveError,
    PageNotFoundError,
    ParentPageNotFoundError,
)
from md2blog.shared.presentation.errors import ErrorCode, ErrorResponse, FieldError


def error_response(
    status_code: int,
    code: ErrorCode,
    message: str,
    *,
    errors: list[FieldError] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(code=code, message=message, errors=errors)
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json", exclude_none=True),
        headers=headers,
    )


async def handle_invalid_credentials(_: Request, __: Exception) -> JSONResponse:
    return error_response(
        status.HTTP_401_UNAUTHORIZED,
        ErrorCode.AUTH_INVALID_CREDENTIALS,
        "이메일 또는 비밀번호가 올바르지 않습니다.",
    )


async def handle_authentication_required(_: Request, __: Exception) -> JSONResponse:
    return error_response(
        status.HTTP_401_UNAUTHORIZED,
        ErrorCode.AUTH_REQUIRED,
        "로그인이 필요합니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def handle_invalid_refresh_token(_: Request, __: Exception) -> JSONResponse:
    return error_response(
        status.HTTP_401_UNAUTHORIZED,
        ErrorCode.AUTH_INVALID_REFRESH_TOKEN,
        "유효하지 않은 리프레시 토큰입니다.",
    )


async def handle_email_already_exists(_: Request, __: Exception) -> JSONResponse:
    return error_response(
        status.HTTP_409_CONFLICT,
        ErrorCode.USER_EMAIL_ALREADY_EXISTS,
        "이미 사용 중인 이메일입니다.",
    )


async def handle_parent_page_not_found(_: Request, __: Exception) -> JSONResponse:
    return error_response(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.WORKSPACE_PARENT_PAGE_NOT_FOUND,
        "상위 페이지를 찾을 수 없습니다.",
    )


async def handle_page_not_found(_: Request, __: Exception) -> JSONResponse:
    return error_response(
        status.HTTP_404_NOT_FOUND,
        ErrorCode.WORKSPACE_PAGE_NOT_FOUND,
        "페이지를 찾을 수 없습니다.",
    )


async def handle_invalid_page_move(_: Request, __: Exception) -> JSONResponse:
    return error_response(
        status.HTTP_409_CONFLICT,
        ErrorCode.WORKSPACE_INVALID_PAGE_MOVE,
        "페이지를 자신의 하위 페이지로 이동할 수 없습니다.",
    )


async def handle_validation_error(_: Request, error: Exception) -> JSONResponse:
    if not isinstance(error, RequestValidationError):
        raise error
    field_errors = [
        FieldError(
            field=".".join(str(part) for part in item["loc"] if part != "body"),
            reason=item["msg"],
        )
        for item in error.errors()
    ]
    return error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        ErrorCode.VALIDATION_ERROR,
        "입력값을 확인해주세요.",
        errors=field_errors,
    )


async def handle_http_exception(_: Request, error: Exception) -> JSONResponse:
    if not isinstance(error, HTTPException):
        raise error
    if error.status_code == status.HTTP_401_UNAUTHORIZED:
        code = ErrorCode.AUTH_REQUIRED
    elif error.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
        code = ErrorCode.SERVICE_UNAVAILABLE
    else:
        code = ErrorCode.HTTP_ERROR
    return error_response(
        error.status_code,
        code,
        str(error.detail),
        headers=error.headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AuthenticationFailedError, handle_invalid_credentials)
    app.add_exception_handler(AuthenticationRequiredError, handle_authentication_required)
    app.add_exception_handler(InvalidAccessTokenError, handle_authentication_required)
    app.add_exception_handler(InvalidRefreshSessionError, handle_invalid_refresh_token)
    app.add_exception_handler(EmailAlreadyExistsError, handle_email_already_exists)
    app.add_exception_handler(ParentPageNotFoundError, handle_parent_page_not_found)
    app.add_exception_handler(PageNotFoundError, handle_page_not_found)
    app.add_exception_handler(InvalidPageMoveError, handle_invalid_page_move)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(HTTPException, handle_http_exception)

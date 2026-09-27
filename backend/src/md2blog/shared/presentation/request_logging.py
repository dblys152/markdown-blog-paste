import logging
import secrets
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from md2blog.shared.infrastructure.logging import (
    REQUEST_ID_HEADER,
    bind_request_id,
    reset_request_id,
)

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = secrets.token_hex(8)
        token = bind_request_id(request_id)
        started_at = perf_counter()
        logger.debug(
            "request started",
            extra={
                "event": "http.request.started",
                "request_method": request.method,
                "request_path": request.url.path,
            },
        )
        try:
            response = await call_next(request)
        except Exception as error:
            logger.error(
                "request failed",
                extra={
                    "event": "http.request.failed",
                    "request_method": request.method,
                    "request_path": request.url.path,
                    "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                    "error_type": type(error).__name__,
                },
            )
            raise
        else:
            status_code = response.status_code
            if status_code >= 500:
                log = logger.error
            elif status_code >= 400:
                log = logger.warning
            else:
                log = logger.info
            log(
                "request completed",
                extra={
                    "event": "http.request.completed",
                    "request_method": request.method,
                    "request_path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                },
            )
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            reset_request_id(token)

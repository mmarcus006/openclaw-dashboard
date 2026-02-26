"""Global exception → standard ErrorResponse envelope.

All unhandled exceptions are caught here and converted to the canonical
error shape defined in models/common.py.
"""

import json
from datetime import datetime, timezone

import structlog
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Error code mapping
# ---------------------------------------------------------------------------

def _build_error_body(
    code: str,
    message: str,
    detail: dict | None = None,
) -> dict:
    """Build the standard error envelope dict.

    Args:
        code: Machine-readable error code (e.g. FILE_NOT_FOUND).
        message: Human-readable description.
        detail: Optional extra context dict.

    Returns:
        Dict matching ErrorResponse schema.
    """
    return {
        "error": {
            "code": code,
            "message": message,
            "detail": detail or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }


def _exception_to_response(exc: Exception) -> JSONResponse:
    """Convert a known exception to a JSONResponse with the right HTTP status.

    Args:
        exc: Any exception.

    Returns:
        JSONResponse with correct status code and error envelope.
    """
    if isinstance(exc, FileNotFoundError):
        return JSONResponse(
            status_code=404,
            content=_build_error_body("FILE_NOT_FOUND", str(exc)),
        )
    if isinstance(exc, PermissionError):
        return JSONResponse(
            status_code=403,
            content=_build_error_body("ACCESS_DENIED", str(exc)),
        )
    if isinstance(exc, json.JSONDecodeError):
        return JSONResponse(
            status_code=422,
            content=_build_error_body("INVALID_JSON", str(exc)),
        )
    if isinstance(exc, ETagMismatchError):
        return JSONResponse(
            status_code=409,
            content=_build_error_body(
                "CONFLICT",
                str(exc),
                {"current_etag": exc.current_etag},
            ),
        )
    if isinstance(exc, TimeoutError):
        return JSONResponse(
            status_code=504,
            content=_build_error_body("GATEWAY_TIMEOUT", str(exc)),
        )
    if isinstance(exc, ValueError):
        return JSONResponse(
            status_code=422,
            content=_build_error_body("VALIDATION_ERROR", str(exc)),
        )

    # Unknown — log with full traceback and return 500
    logger.error("Unhandled exception", exc_info=exc, exc_type=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content=_build_error_body("INTERNAL_ERROR", "An internal server error occurred."),
    )


class ETagMismatchError(Exception):
    """Raised when an If-Match ETag does not match the current file ETag.

    Attributes:
        current_etag: The current ETag of the file on disk.
    """

    def __init__(self, message: str, current_etag: str = "") -> None:
        """Initialise with a message and the current ETag value.

        Args:
            message: Human-readable description.
            current_etag: The current ETag value the client should use next.
        """
        super().__init__(message)
        self.current_etag = current_etag


class GlobalExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware that catches every unhandled exception and returns the standard error envelope.

    This is a backstop — route-level handlers should catch domain errors first.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Forward the request and catch any unhandled exception.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware/handler in the chain.

        Returns:
            Upstream response, or a JSONResponse error envelope if an exception occurred.
        """
        try:
            return await call_next(request)
        except Exception as exc:  # noqa: BLE001
            return _exception_to_response(exc)


# ---------------------------------------------------------------------------
# FastAPI exception handlers (registered in main.py)
# ---------------------------------------------------------------------------

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Convert FastAPI HTTPException to the standard error envelope.

    Args:
        request: The request that triggered the exception.
        exc: The HTTPException instance.

    Returns:
        JSONResponse with standard error body.
    """
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "ACCESS_DENIED",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        504: "GATEWAY_TIMEOUT",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    detail = exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_body(code, str(exc.detail), detail),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert Pydantic request-validation errors to the standard error envelope.

    Args:
        request: The request that triggered the exception.
        exc: The RequestValidationError instance.

    Returns:
        JSONResponse with validation details.
    """
    return JSONResponse(
        status_code=422,
        content=_build_error_body(
            "VALIDATION_ERROR",
            "Request validation failed.",
            {"errors": exc.errors()},
        ),
    )

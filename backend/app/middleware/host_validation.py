"""Host header validation middleware — DNS rebinding protection (R5)."""

import logging
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.utils import now_iso

logger = logging.getLogger(__name__)

# Allow extra hosts via DASHBOARD_ALLOWED_HOSTS env var (comma-separated).
# Useful for Tailscale remote access: DASHBOARD_ALLOWED_HOSTS=miller-mac.taila54727.ts.net
_extra = os.environ.get("DASHBOARD_ALLOWED_HOSTS", "")
_extra_hosts = frozenset(h.strip().lower() for h in _extra.split(",") if h.strip())
ALLOWED_HOSTS = frozenset(["localhost", "127.0.0.1"]) | _extra_hosts


class HostValidationMiddleware(BaseHTTPMiddleware):
    """Reject any request whose Host header is not localhost / 127.0.0.1.

    Prevents DNS rebinding attacks where evil.com resolves to 127.0.0.1
    and attempts to call the local API from a malicious browser tab.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Validate Host header before forwarding the request.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware/handler in the chain.

        Returns:
            403 JSON response if host is invalid; otherwise the upstream response.
        """
        host_header = request.headers.get("host", "")
        # Strip port from host (e.g. "localhost:8400" → "localhost")
        host = host_header.split(":")[0].lower()

        if host not in ALLOWED_HOSTS:
            logger.warning("Rejected request with invalid Host header: %s", host_header)
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": "INVALID_HOST",
                        "message": f"Host '{host_header}' is not allowed. "
                                   "Only localhost connections are permitted.",
                        "detail": {"host": host_header},
                        "timestamp": now_iso(),
                    }
                },
            )

        return await call_next(request)



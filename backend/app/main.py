"""FastAPI application entry point.

Responsibilities:
  - Configure structlog with JSON output.
  - Run startup validation (OPENCLAW_HOME, config, main workspace).
  - Register middleware: Host validation (R5), Global exception handler.
  - Configure CORS (http://localhost:5173 ONLY — never *).
  - Include all routers under /api.
  - Mount WebSocket at /ws/live.
  - Serve static frontend files in production.
"""

import logging
import shutil
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import Depends, FastAPI, WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.utils import limiter
from app.dependencies import get_agent_service, get_gateway_service
from app.middleware.error_handler import (
    GlobalExceptionHandlerMiddleware,
    http_exception_handler,
    validation_exception_handler,
)
from app.middleware.host_validation import HostValidationMiddleware
from app.routers import agents, config, cron, gateway, health
from app.services.agent_service import AgentService
from app.services.gateway_service import GatewayService
from app.websocket.live import websocket_handler

# ---------------------------------------------------------------------------
# Logging — configure structlog with JSON output
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------


class SystemStatus:
    """Mutable container for startup validation results."""

    openclaw_home_ok: bool = False
    config_ok: bool = False
    workspace_ok: bool = False
    gateway_cli_ok: bool = False


system_status = SystemStatus()


def _run_startup_validation() -> None:
    """Validate the runtime environment at startup.

    Logs warnings for any missing or malformed components.  Sets flags on
    the global `system_status` object so /api/health can reflect reality.
    Does NOT raise — the dashboard should start even in a degraded state
    and show clear error states in the UI.
    """
    import json as _json

    # 1. OPENCLAW_HOME exists
    home = settings.OPENCLAW_HOME
    if not home.exists():
        logger.warning("startup_validation", check="openclaw_home", result="MISSING", path=str(home))
    else:
        system_status.openclaw_home_ok = True
        logger.info("startup_validation", check="openclaw_home", result="OK")

    # 2. openclaw.json is valid JSON
    config_path = settings.config_path
    if not config_path.exists():
        logger.warning("startup_validation", check="config", result="MISSING", path=str(config_path))
    else:
        try:
            _json.loads(config_path.read_text(encoding="utf-8"))
            system_status.config_ok = True
            logger.info("startup_validation", check="config", result="OK")
        except _json.JSONDecodeError as exc:
            logger.warning("startup_validation", check="config", result="INVALID_JSON", error=str(exc))

    # 3. Main workspace exists
    ws = settings.workspace
    if not ws.exists():
        logger.warning("startup_validation", check="main_workspace", result="MISSING", path=str(ws))
    else:
        system_status.workspace_ok = True
        logger.info("startup_validation", check="main_workspace", result="OK")

    # 4. openclaw CLI available
    if shutil.which("openclaw") is None:
        logger.warning("startup_validation", check="gateway_cli", result="NOT_IN_PATH")
    else:
        system_status.gateway_cli_ok = True
        logger.info("startup_validation", check="gateway_cli", result="OK")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler — startup validation.

    Args:
        app: The FastAPI application instance.
    """
    _run_startup_validation()
    logger.info(
        "dashboard_startup",
        host=settings.HOST,
        port=settings.PORT,
        openclaw_home=str(settings.OPENCLAW_HOME),
    )
    yield
    logger.info("dashboard_shutdown")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance.
    """
    app = FastAPI(
        title="OpenClaw Dashboard API",
        description=(
            "REST + WebSocket API for managing the OpenClaw multi-agent ecosystem.  "
            "Personal-use only (localhost). "
            "See /docs for full API reference."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ------------------------------------------------------------------
    # Rate limiter
    # ------------------------------------------------------------------
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ------------------------------------------------------------------
    # Middleware (order matters — outermost registered LAST with add_middleware)
    # Host validation must run BEFORE CORS to reject DNS rebinding early.
    # ------------------------------------------------------------------
    app.add_middleware(GlobalExceptionHandlerMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Vite dev server ONLY
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.add_middleware(HostValidationMiddleware)

    # ------------------------------------------------------------------
    # Exception handlers (FastAPI-level — for HTTPException + validation)
    # ------------------------------------------------------------------
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    api_prefix = "/api"
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(agents.router, prefix=api_prefix)
    app.include_router(config.router, prefix=api_prefix)
    app.include_router(gateway.router, prefix=api_prefix)
    app.include_router(cron.router, prefix=api_prefix)

    # ------------------------------------------------------------------
    # WebSocket
    # ------------------------------------------------------------------
    @app.websocket("/ws/live")
    async def ws_live(
        websocket: WebSocket,
        agent_svc: AgentService = Depends(get_agent_service),
        gateway_svc: GatewayService = Depends(get_gateway_service),
    ) -> None:
        """WebSocket endpoint for live updates.

        Args:
            websocket: Incoming WebSocket connection.
            agent_svc: AgentService (injected).
            gateway_svc: GatewayService (injected).
        """
        await websocket_handler(websocket, agent_svc, gateway_svc)

    # ------------------------------------------------------------------
    # Static file serving (production build)
    # ------------------------------------------------------------------
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
        logger.info("static_files_mounted", path=str(static_dir))

    return app


# Module-level app instance
app = create_app()

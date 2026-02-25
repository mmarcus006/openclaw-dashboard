"""Health check router — GET /api/health."""

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends

from app.config import Settings
from app.dependencies import get_settings
from app.models.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Returns the overall health of the dashboard backend and "
        "a per-subsystem status map. A subsystem is True when it is "
        "reachable/valid, False when degraded."
    ),
    status_code=200,
)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return backend health and subsystem statuses.

    Args:
        settings: Application settings (injected).

    Returns:
        HealthResponse with status, version, and subsystem map.
    """
    subsystems = {
        "config": _check_config(settings),
        "workspaces": _check_workspaces(settings),
        "gateway_cli": _check_gateway_cli(),
        "sessions": _check_sessions(settings),
    }

    overall = "ok" if all(subsystems.values()) else "degraded"

    return HealthResponse(
        status=overall,
        version="1.0.0",
        openclaw_home=str(settings.OPENCLAW_HOME),
        subsystems=subsystems,
    )


# ---------------------------------------------------------------------------
# Subsystem checks
# ---------------------------------------------------------------------------

def _check_config(settings: Settings) -> bool:
    """Return True if openclaw.json exists and is non-empty."""
    try:
        p = settings.config_path
        return p.exists() and p.stat().st_size > 0
    except OSError:
        return False


def _check_workspaces(settings: Settings) -> bool:
    """Return True if at least the main workspace directory exists."""
    try:
        return settings.workspace.exists() and settings.workspace.is_dir()
    except OSError:
        return False


def _check_gateway_cli() -> bool:
    """Return True if the openclaw CLI is findable in PATH."""
    return shutil.which("openclaw") is not None


def _check_sessions(settings: Settings) -> bool:
    """Return True if the sessions directory or file is accessible."""
    try:
        sessions_dir = settings.sessions_path.parent
        return sessions_dir.exists()
    except OSError:
        return False

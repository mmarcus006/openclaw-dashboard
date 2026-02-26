"""Gateway router — /api/gateway/*

All subprocess calls use create_subprocess_exec with enum-validated
actions — never create_subprocess_shell with string interpolation (R6).
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies import get_gateway_service
from app.models.gateway import (
    CommandResponse,
    GatewayAction,
    GatewayHistoryResponse,
    GatewayStatusResponse,
)
from app.services.gateway_service import GatewayService
from app.utils import limiter

router = APIRouter(prefix="/gateway", tags=["gateway"])


@router.get(
    "/status",
    response_model=GatewayStatusResponse,
    summary="Get gateway status",
    description=(
        "Run ``openclaw gateway status`` and return parsed status.  "
        "Returns a degraded response (running=False, error=...) if the "
        "CLI is unavailable or output cannot be parsed."
    ),
    status_code=status.HTTP_200_OK,
)
async def get_gateway_status(
    gateway_svc: GatewayService = Depends(get_gateway_service),
) -> GatewayStatusResponse:
    """Return current gateway daemon status.

    Args:
        gateway_svc: GatewayService (injected).

    Returns:
        GatewayStatusResponse (degraded if CLI unavailable).
    """
    return await gateway_svc.get_status()


@router.post(
    "/{action}",
    response_model=CommandResponse,
    summary="Execute a gateway command",
    description=(
        "Run start, stop, or restart on the OpenClaw gateway daemon.  "
        "The action is validated against the GatewayAction enum before "
        "the subprocess is executed — no shell interpolation occurs."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Invalid action"},
        504: {"description": "Gateway command timed out"},
    },
)
@limiter.limit("5/minute")
async def gateway_command(
    action: GatewayAction,
    request: Request,
    gateway_svc: GatewayService = Depends(get_gateway_service),
) -> CommandResponse:
    """Execute a gateway control command.

    The ``action`` path parameter is validated by FastAPI via the
    GatewayAction enum — FastAPI returns 422 automatically for invalid
    values before this function is called.

    Args:
        action: One of GatewayAction.START, STOP, or RESTART (enum-validated).
        request: Raw request (available for rate limiter decorator if needed).
        gateway_svc: GatewayService (injected).

    Returns:
        CommandResponse indicating success and output.

    Raises:
        HTTPException 404: If the openclaw CLI is not found.
        HTTPException 504: If the subprocess times out.
    """
    try:
        return await gateway_svc.run_command(action)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc


@router.get(
    "/history",
    response_model=GatewayHistoryResponse,
    summary="Get gateway command history",
    description="Return last 10 gateway commands (in-memory, resets on restart).",
    status_code=status.HTTP_200_OK,
)
async def get_gateway_history(
    gateway_svc: GatewayService = Depends(get_gateway_service),
) -> GatewayHistoryResponse:
    """Return recent gateway command history."""
    return gateway_svc.get_history()

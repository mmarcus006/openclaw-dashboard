"""Config router — /api/config/*

Manages read/write of openclaw.json with ETag concurrency control and
backup rotation via ConfigService.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.dependencies import get_config_service
from app.middleware.error_handler import ETagMismatchError
from app.models.config import (
    ConfigResponse,
    ConfigValidateResponse,
    ConfigWriteRequest,
)
from app.services.config_service import ConfigService

router = APIRouter(prefix="/config", tags=["config"])


@router.get(
    "",
    response_model=ConfigResponse,
    summary="Read OpenClaw configuration",
    description=(
        "Return the full openclaw.json with secret values redacted.  "
        "The response includes an ETag that must be passed as If-Match on "
        "subsequent write requests to prevent overwrite conflicts."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "openclaw.json not found"},
    },
)
async def get_config(
    config_svc: ConfigService = Depends(get_config_service),
) -> ConfigResponse:
    """Return the current OpenClaw configuration.

    Args:
        config_svc: ConfigService (injected).

    Returns:
        ConfigResponse with redacted config dict and ETag.

    Raises:
        HTTPException 404: If openclaw.json does not exist.
        HTTPException 422: If the file is not valid JSON.
    """
    try:
        return await config_svc.read_config()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # JSONDecodeError etc.  noqa: BLE001
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put(
    "",
    response_model=ConfigResponse,
    summary="Write OpenClaw configuration",
    description=(
        "Overwrite openclaw.json with the supplied config.  Requires an "
        "If-Match header with the ETag from the last GET.  Creates a "
        "timestamped backup before writing; keeps at most 10 backups.  "
        "Values sent as __REDACTED__ are preserved from the original file."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        409: {"description": "ETag mismatch — file changed externally"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def put_config(
    request: Request,
    body: ConfigWriteRequest,
    if_match: str | None = Header(None, alias="if-match", description="ETag from last GET"),
    config_svc: ConfigService = Depends(get_config_service),
) -> ConfigResponse:
    """Write a new openclaw.json configuration.

    Args:
        request: Raw request (needed for rate limiter).
        body: ConfigWriteRequest containing the config dict and optional ETag.
        if_match: If-Match header for concurrency control.
        config_svc: ConfigService (injected).

    Returns:
        ConfigResponse with the newly written config and new ETag.

    Raises:
        HTTPException 409: ETag mismatch.
        HTTPException 422: Invalid JSON structure.
    """
    # Merge ETag from header (takes precedence) or body
    etag_to_use = if_match.strip('"') if if_match else body.etag

    write_request = ConfigWriteRequest(config=body.config, etag=etag_to_use)

    try:
        return await config_svc.write_config(write_request)
    except ETagMismatchError as exc:
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "CONFLICT",
                    "message": str(exc),
                    "detail": {"current_etag": exc.current_etag},
                    "timestamp": _now_iso(),
                }
            },
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/validate",
    response_model=ConfigValidateResponse,
    summary="Validate configuration without saving",
    description=(
        "Validate a configuration JSON object against known rules.  "
        "Does not write to disk.  Returns a list of errors and warnings."
    ),
    status_code=status.HTTP_200_OK,
)
async def validate_config(
    body: ConfigWriteRequest,
    config_svc: ConfigService = Depends(get_config_service),
) -> ConfigValidateResponse:
    """Validate a config object without persisting it.

    Args:
        body: ConfigWriteRequest containing the config dict to validate.
        config_svc: ConfigService (injected).

    Returns:
        ConfigValidateResponse with valid flag and error/warning lists.
    """
    return await config_svc.validate_config(body.config)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()

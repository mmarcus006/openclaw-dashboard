"""Agents router — /api/agents/*

File paths are always passed as query parameters (R1) — never as URL
path segments.  This avoids URL routing ambiguity with path separators
and special characters.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse

from app.dependencies import get_agent_service, get_file_service
from app.middleware.error_handler import ETagMismatchError
from app.models.agent import AgentDetailResponse, AgentListResponse
from app.models.common import FileContentResponse, SaveResponse
from app.models.file import FileListResponse
from app.services.agent_service import AgentService
from app.services.file_service import FileService
from app.utils import now_iso

router = APIRouter(prefix="/agents", tags=["agents"])


# ---------------------------------------------------------------------------
# Agent listing / detail
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=AgentListResponse,
    summary="List all agents",
    description=(
        "Discover all configured OpenClaw agents from the filesystem and "
        "openclaw.json.  Returns summary information including status and "
        "last activity."
    ),
    status_code=status.HTTP_200_OK,
)
async def list_agents(
    agent_svc: AgentService = Depends(get_agent_service),
) -> AgentListResponse:
    """Return a list of all discovered agents.

    Args:
        agent_svc: AgentService (injected).

    Returns:
        AgentListResponse with all agents.
    """
    return await agent_svc.list_agents()


@router.get(
    "/{agent_id}",
    response_model=AgentDetailResponse,
    summary="Get agent detail",
    description=(
        "Return full detail for a single agent including workspace path, "
        "file list, last activity, and status."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Agent or workspace not found"},
    },
)
async def get_agent(
    agent_id: str,
    agent_svc: AgentService = Depends(get_agent_service),
) -> AgentDetailResponse:
    """Return detailed information for a specific agent.

    Args:
        agent_id: Unique agent identifier from the URL.
        agent_svc: AgentService (injected).

    Returns:
        AgentDetailResponse with workspace files and metadata.

    Raises:
        HTTPException 404: If the agent workspace is not found.
    """
    try:
        return await agent_svc.get_agent(agent_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# File read/write (R1: path as query parameter)
# ---------------------------------------------------------------------------


@router.get(
    "/{agent_id}/files/browse",
    response_model=FileListResponse,
    summary="List files in agent workspace",
    description="List files in an agent's workspace with optional recursive scanning.",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Agent workspace not found"},
    },
)
async def list_agent_files(
    agent_id: str,
    recursive: bool = Query(False, description="Scan subdirectories recursively"),
    depth: int = Query(2, ge=1, le=3, description="Max directory depth (1-3)"),
    max_files: int = Query(200, ge=1, le=500, description="Max files to return"),
    agent_svc: AgentService = Depends(get_agent_service),
) -> FileListResponse:
    """List files in an agent's workspace.

    Args:
        agent_id: Agent identifier from URL.
        recursive: Whether to scan subdirectories recursively.
        depth: Maximum directory depth (1-3, server enforces hard ceiling of 3).
        max_files: Maximum number of files to return (1-500).
        agent_svc: AgentService (injected).

    Returns:
        FileListResponse with file entries and truncation flag.

    Raises:
        HTTPException 404: If the agent workspace is not found.
    """
    try:
        return await agent_svc.list_workspace_files_recursive(
            agent_id,
            recursive=recursive,
            depth=depth,
            max_files=max_files,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/{agent_id}/files",
    response_model=FileContentResponse,
    summary="Read agent workspace file",
    description=(
        "Read a file from an agent's workspace.  The file path is passed "
        "as a query parameter (not a URL path segment).  Returns the file "
        "content plus an ETag header for concurrency control on subsequent "
        "writes."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "File not found"},
        403: {"description": "Path outside sandbox"},
    },
)
async def read_agent_file(
    agent_id: str,
    response: Response,
    path: str = Query(..., description="File path relative to the agent's workspace"),
    agent_svc: AgentService = Depends(get_agent_service),
    file_svc: FileService = Depends(get_file_service),
) -> FileContentResponse:
    """Read a file from an agent's workspace.

    Args:
        agent_id: Agent identifier from URL.
        response: FastAPI response object (used to set ETag header).
        path: File path relative to the agent's workspace (query param).
        agent_svc: AgentService (injected).
        file_svc: FileService (injected).

    Returns:
        FileContentResponse with content, size, mtime, and language hint.

    Raises:
        HTTPException 404: If the file does not exist.
        HTTPException 403: If the resolved path is outside the sandbox.
    """
    workspace = agent_svc.resolve_agent_workspace(agent_id)
    full_path = _resolve_workspace_path(workspace, path)

    try:
        content, etag = await file_svc.read_file(full_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    stat = full_path.stat()
    from datetime import datetime, timezone

    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

    # Set ETag header so the frontend can use it in If-Match on write
    response.headers["ETag"] = f'"{etag}"'

    return FileContentResponse(
        path=path,
        content=content,
        size=stat.st_size,
        mtime=mtime,
        language=file_svc.detect_language(path),
    )


@router.put(
    "/{agent_id}/files",
    response_model=SaveResponse,
    summary="Write agent workspace file",
    description=(
        "Write content to a file in an agent's workspace.  Requires an "
        "If-Match header containing the ETag returned by the GET request.  "
        "Returns 409 Conflict if the file was modified since it was last read."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        409: {"description": "ETag mismatch — file changed externally"},
        403: {"description": "Path outside sandbox or read-only"},
        404: {"description": "Agent workspace not found"},
    },
)
async def write_agent_file(
    agent_id: str,
    response: Response,
    body: dict,
    path: str = Query(..., description="File path relative to the agent's workspace"),
    if_match: str | None = Header(None, alias="if-match", description="ETag from last GET"),
    agent_svc: AgentService = Depends(get_agent_service),
    file_svc: FileService = Depends(get_file_service),
) -> SaveResponse:
    """Write content to a file in an agent's workspace.

    Args:
        agent_id: Agent identifier from URL.
        response: FastAPI response object (used to set new ETag header).
        body: JSON body with "content" key.
        path: File path relative to the agent's workspace (query param).
        if_match: If-Match header for ETag concurrency control.
        agent_svc: AgentService (injected).
        file_svc: FileService (injected).

    Returns:
        SaveResponse with the new ETag, size, and mtime.

    Raises:
        HTTPException 400: Missing "content" in request body.
        HTTPException 403: Path outside sandbox.
        HTTPException 409: ETag mismatch.
    """
    content = body.get("content")
    if content is None:
        raise HTTPException(
            status_code=400, detail='Request body must contain a "content" key.'
        )

    workspace = agent_svc.resolve_agent_workspace(agent_id)
    full_path = _resolve_workspace_path(workspace, path)

    # Strip surrounding quotes from If-Match (HTTP spec wraps in double-quotes)
    clean_if_match = if_match.strip('"') if if_match else None

    try:
        new_etag = await file_svc.write_file(full_path, str(content), clean_if_match)
    except ETagMismatchError as exc:
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "CONFLICT",
                    "message": str(exc),
                    "detail": {"current_etag": exc.current_etag, "path": path},
                    "timestamp": now_iso(),
                }
            },
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    stat = full_path.stat()
    from datetime import datetime, timezone

    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

    response.headers["ETag"] = f'"{new_etag}"'

    return SaveResponse(
        path=path,
        size=stat.st_size,
        mtime=mtime,
        etag=new_etag,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_workspace_path(workspace: Path, relative_path: str) -> Path:
    """Build the absolute path inside a workspace from a relative path string.

    Rejects any path that would escape the workspace via ../ traversal
    (the FileService will also check the resolved path against the global
    sandbox, so this is a belt-and-suspenders guard).

    Args:
        workspace: Absolute path to the agent's workspace directory.
        relative_path: Relative path string from the query parameter.

    Returns:
        Absolute Path inside the workspace.

    Raises:
        HTTPException 400: If the path contains traversal sequences.
    """
    # Reject obvious traversal attempts early
    if ".." in Path(relative_path).parts:
        raise HTTPException(
            status_code=400,
            detail=f"Path traversal not allowed: {relative_path!r}",
        )
    return workspace / relative_path



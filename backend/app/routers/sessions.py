"""Sessions router — /api/agents/{agent_id}/sessions and /api/sessions/{session_id}/messages

Session list is accessed through agent context.
Session messages are accessed by session key (which contains colons).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_session_service
from app.models.session import SessionListResponse, SessionMessageListResponse
from app.services.session_service import SessionService

router = APIRouter(tags=["sessions"])


@router.get(
    "/agents/{agent_id}/sessions",
    response_model=SessionListResponse,
    summary="List sessions for an agent",
    description=(
        "Return paginated sessions for the given agent, sorted by "
        "updatedAt descending.  Filters by session key prefix "
        "agent:{agent_id}: to find all sessions for the agent."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        413: {"description": "sessions.json exceeds 50MB"},
    },
)
async def list_sessions(
    agent_id: str,
    limit: int = Query(20, ge=1, le=100, description="Max sessions to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session_svc: SessionService = Depends(get_session_service),
) -> SessionListResponse:
    """List sessions for a specific agent.

    Args:
        agent_id: Agent identifier from URL.
        limit: Maximum number of sessions to return.
        offset: Number of sessions to skip.
        session_svc: SessionService (injected).

    Returns:
        SessionListResponse with paginated session summaries.
    """
    if await session_svc.check_file_too_large():
        raise HTTPException(
            status_code=413,
            detail="sessions.json exceeds maximum allowed size (50MB)",
        )
    return await session_svc.list_sessions(agent_id, limit=limit, offset=offset)


@router.get(
    "/sessions/{session_id:path}/messages",
    response_model=SessionMessageListResponse,
    summary="Get messages from a session",
    description=(
        "Parse the JSONL file for the given session and return paginated "
        "messages.  Only entries with type=='message' are included.  "
        "Missing/deleted session files return 200 with a warning."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Path traversal detected"},
    },
)
async def get_session_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=200, description="Max messages to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    full: bool = Query(False, description="Include full content without truncation"),
    session_svc: SessionService = Depends(get_session_service),
) -> SessionMessageListResponse:
    """Get messages from a session JSONL file.

    Args:
        session_id: Session key (e.g., agent:main:main).
        limit: Maximum number of messages to return.
        offset: Number of messages to skip.
        full: If true, include full content blocks without truncation.
        session_svc: SessionService (injected).

    Returns:
        SessionMessageListResponse with parsed messages.
    """
    # Path traversal check
    if ".." in session_id:
        raise HTTPException(
            status_code=403,
            detail="Path traversal not allowed",
        )
    return await session_svc.get_messages(session_id, limit=limit, offset=offset, full=full)

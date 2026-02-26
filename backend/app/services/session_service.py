"""Session service — reads sessions.json and JSONL session files.

Provides session list (from sessions.json) and message parsing (from JSONL).
Implements caching with file-mtime invalidation and selective field extraction
to skip the large skillsSnapshot field.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

import structlog

from app.config import Settings
from app.models.session import (
    ContentBlock,
    SessionListResponse,
    SessionMessage,
    SessionMessageListResponse,
    SessionSummary,
)

logger = structlog.get_logger(__name__)

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
_THREAD_THRESHOLD = 1 * 1024 * 1024  # 1MB
_DEFAULT_CONTENT_TRUNCATION = 2000


class SessionService:
    """Read and parse OpenClaw session data."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cache: dict[str, Any] = {}
        self._cache_mtime: float | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def list_sessions(
        self,
        agent_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> SessionListResponse:
        """List sessions for an agent from sessions.json.

        Args:
            agent_id: Agent identifier to filter by.
            limit: Max sessions to return.
            offset: Pagination offset.

        Returns:
            SessionListResponse with filtered, sorted sessions.
        """
        raw = await self._load_sessions_cached()
        if raw is None:
            return SessionListResponse(sessions=[], total=0)

        # Check for format version
        warning = None
        if isinstance(raw, dict) and "version" in raw:
            version = raw.get("version")
            if version is not None:
                warning = f"Unknown session format version {version}"

        # Filter by agent key prefix
        prefix = f"agent:{agent_id}:"
        entries: list[tuple[str, dict]] = []
        for key, value in raw.items():
            if key == "version":
                continue
            if not key.startswith(prefix):
                continue
            if not isinstance(value, dict):
                continue
            entries.append((key, value))

        # Sort by updatedAt descending
        entries.sort(
            key=lambda kv: kv[1].get("updatedAt", 0) if isinstance(kv[1].get("updatedAt"), (int, float)) else 0,
            reverse=True,
        )

        total = len(entries)
        page = entries[offset : offset + limit]

        summaries = []
        for key, data in page:
            summaries.append(self._build_summary(key, data))

        return SessionListResponse(
            sessions=summaries,
            total=total,
            warning=warning,
        )

    async def get_messages(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        full: bool = False,
    ) -> SessionMessageListResponse:
        """Read messages from a session JSONL file.

        Args:
            session_id: Session key (e.g., "agent:main:main").
            limit: Max messages to return.
            offset: Pagination offset (counts message entries only).
            full: If True, include full content text without truncation.

        Returns:
            SessionMessageListResponse with parsed messages.
        """
        # Look up session file path from sessions.json
        raw = await self._load_sessions_cached()
        if raw is None or session_id not in raw:
            return SessionMessageListResponse(
                messages=[],
                total=0,
                has_more=False,
                warning="Session not found in registry",
            )

        session_data = raw.get(session_id, {})
        if not isinstance(session_data, dict):
            return SessionMessageListResponse(
                messages=[], total=0, has_more=False,
                warning="Invalid session data",
            )

        session_file = session_data.get("sessionFile")
        if not session_file:
            return SessionMessageListResponse(
                messages=[], total=0, has_more=False,
                warning="No session file path in registry",
            )

        session_path = Path(session_file)

        # Security: validate path is under OPENCLAW_HOME
        try:
            session_path.resolve().relative_to(self._settings.OPENCLAW_HOME.resolve())
        except ValueError:
            return SessionMessageListResponse(
                messages=[], total=0, has_more=False,
                warning="Session file path outside allowed directory",
            )

        # Handle missing/deleted files gracefully
        if not session_path.exists():
            return SessionMessageListResponse(
                messages=[], total=0, has_more=False,
                warning="Session file not found (session may have been archived)",
            )

        # Check file size
        try:
            file_size = session_path.stat().st_size
        except OSError:
            return SessionMessageListResponse(
                messages=[], total=0, has_more=False,
                warning="Cannot read session file",
            )

        if file_size > _MAX_FILE_SIZE:
            return SessionMessageListResponse(
                messages=[], total=0, has_more=False,
                warning=f"Session file too large ({file_size / 1024 / 1024:.1f}MB, max 50MB)",
            )

        return await self._parse_jsonl(session_path, limit, offset, full)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _load_sessions_cached(self) -> dict | None:
        """Load sessions.json with mtime-based cache invalidation."""
        sessions_path = self._settings.sessions_path
        if not sessions_path.exists():
            self._cache = {}
            self._cache_mtime = None
            return None

        try:
            current_mtime = sessions_path.stat().st_mtime
        except OSError:
            return None

        if self._cache_mtime == current_mtime and self._cache:
            return self._cache

        # Check file size
        try:
            file_size = sessions_path.stat().st_size
        except OSError:
            return None

        if file_size > _MAX_FILE_SIZE:
            logger.warning("sessions_json_too_large", size=file_size)
            return None  # Will be handled by caller

        try:
            content = sessions_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("sessions_read_error", error=str(exc))
            return None

        if not content.strip():
            self._cache = {}
            self._cache_mtime = current_mtime
            return {}

        try:
            if file_size > _THREAD_THRESHOLD:
                data = await asyncio.to_thread(json.loads, content)
            else:
                data = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.warning("sessions_json_parse_error", error=str(exc))
            return None

        if not isinstance(data, dict):
            return None

        # Cache the raw dict — skillsSnapshot is skipped at extraction time
        self._cache = data
        self._cache_mtime = current_mtime
        return data

    async def check_file_too_large(self) -> bool:
        """Check if sessions.json exceeds the size limit."""
        sessions_path = self._settings.sessions_path
        if not sessions_path.exists():
            return False
        try:
            return sessions_path.stat().st_size > _MAX_FILE_SIZE
        except OSError:
            return False

    def invalidate_cache(self) -> None:
        """Clear the sessions.json cache."""
        self._cache = {}
        self._cache_mtime = None

    def _build_summary(self, key: str, data: dict) -> SessionSummary:
        """Build a SessionSummary from a sessions.json entry, skipping skillsSnapshot."""
        return SessionSummary(
            session_id=key,
            updated_at=data.get("updatedAt", 0),
            model=data.get("model"),
            model_provider=data.get("modelProvider"),
            label=(
                data.get("label")
                or (data.get("origin", {}).get("label") if isinstance(data.get("origin"), dict) else data.get("label"))
            ),
            spawned_by=data.get("spawnedBy"),
            total_tokens=data.get("totalTokens"),
            input_tokens=data.get("inputTokens"),
            output_tokens=data.get("outputTokens"),
            cache_read=data.get("cacheRead"),
            session_file=data.get("sessionFile"),
        )

    async def _parse_jsonl(
        self,
        path: Path,
        limit: int,
        offset: int,
        full: bool,
    ) -> SessionMessageListResponse:
        """Parse a JSONL session file and extract messages."""
        messages: list[SessionMessage] = []
        skipped_lines = 0
        total_messages = 0

        try:
            content = await asyncio.to_thread(path.read_text, "utf-8", "replace")
        except OSError as exc:
            return SessionMessageListResponse(
                messages=[], total=0, has_more=False,
                warning=f"Cannot read session file: {exc}",
            )

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                skipped_lines += 1
                continue

            if not isinstance(entry, dict):
                skipped_lines += 1
                continue

            if entry.get("type") != "message":
                skipped_lines += 1
                continue

            total_messages += 1

            # Pagination: skip until offset
            if total_messages <= offset:
                continue

            # Collect up to limit messages
            if len(messages) >= limit:
                continue

            msg_data = entry.get("message", {})
            if not isinstance(msg_data, dict):
                continue

            role = msg_data.get("role", "unknown")
            raw_content = msg_data.get("content", [])
            if not isinstance(raw_content, list):
                raw_content = []

            blocks = self._parse_content_blocks(raw_content)
            content_text = self._extract_content_text(blocks)

            if not full and content_text and len(content_text) > _DEFAULT_CONTENT_TRUNCATION:
                content_text = content_text[:_DEFAULT_CONTENT_TRUNCATION] + "..."

            messages.append(
                SessionMessage(
                    id=entry.get("id", ""),
                    role=role,
                    content=blocks if full else [],
                    content_text=content_text,
                    timestamp=entry.get("timestamp"),
                    parent_id=entry.get("parentId"),
                )
            )

        has_more = total_messages > offset + limit

        return SessionMessageListResponse(
            messages=messages,
            total=total_messages,
            has_more=has_more,
            skipped_lines=skipped_lines,
        )

    def _parse_content_blocks(self, raw_blocks: list) -> list[ContentBlock]:
        """Parse raw content block dicts into ContentBlock models."""
        blocks = []
        for raw in raw_blocks:
            if not isinstance(raw, dict):
                continue
            block_type = raw.get("type", "text")
            blocks.append(
                ContentBlock(
                    type=block_type,
                    text=raw.get("text"),
                    thinking=raw.get("thinking"),
                    id=raw.get("id"),
                    name=raw.get("name"),
                    arguments=raw.get("arguments"),
                    tool_call_id=raw.get("toolCallId"),
                    content=raw.get("content") if block_type == "toolResult" else None,
                )
            )
        return blocks

    def _extract_content_text(self, blocks: list[ContentBlock]) -> str:
        """Concatenate text from all text/thinking blocks."""
        parts = []
        for block in blocks:
            text = block.extract_text()
            if text:
                parts.append(text)
        return "\n\n".join(parts)

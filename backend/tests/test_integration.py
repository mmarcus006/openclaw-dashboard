"""Integration tests to boost coverage from 78% to 85%+.

Targets uncovered lines in:
  - session_service.py (76% → ~95%): JSONL parsing edge cases, content blocks,
    truncation, corrupt data, session-not-found paths, cache edge cases.
  - gateway_service.py (73% → ~95%): CLI not found, timeout, parse_status
    branches, run_command paths, history, is_installed.
  - routers/sessions.py (73% → ~95%): messages endpoint via HTTP, path traversal.
  - routers/health.py (80% → ~95%): degraded subsystem states.
  - file_service.py (81% → ~95%): write with directory creation, ETag mismatch,
    binary detection, compute_etag, get_mtime.
  - config_service.py (84% → ~95%): backup creation, backup pruning, write
    with missing path, validate edge cases.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.config import Settings
from app.middleware.error_handler import ETagMismatchError
from app.models.gateway import GatewayAction
from app.services.config_service import ConfigService, _redact_secrets, _restore_redacted
from app.services.file_service import FileService
from app.services.gateway_service import (
    GatewayService,
    _detect_running,
    _extract_channels,
    _extract_pid,
    _extract_uptime,
)
from app.services.session_service import SessionService


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    """Write JSONL entries to a file."""
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def _make_session_env(tmp_path: Path, sessions_data: dict | None = None) -> tuple[Path, Settings]:
    """Create a minimal openclaw home with sessions support.

    Returns (home_path, Settings).
    """
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    if sessions_data is not None:
        (sessions_dir / "sessions.json").write_text(json.dumps(sessions_data))
    settings = Settings(OPENCLAW_HOME=tmp_path)
    return tmp_path, settings


# ===========================================================================
# SESSION SERVICE — uncovered lines
# ===========================================================================


class TestSessionServiceContentBlocks:
    """Test JSONL parsing with different content block types."""

    async def test_tool_result_content_block(self, tmp_path: Path) -> None:
        """toolResult blocks are parsed with content field."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {
                "sessionId": "s1",
                "updatedAt": 1000,
                "sessionFile": str(tmp_path / "sessions" / "s1.jsonl"),
            }
        })
        _write_jsonl(tmp_path / "sessions" / "s1.jsonl", [
            {
                "type": "message", "id": "msg-1",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "toolResult", "toolCallId": "tc-1", "content": "file contents here"},
                    ],
                },
            },
        ])
        svc = SessionService(settings=settings)
        result = await svc.get_messages("agent:main:main", full=True)
        assert result.total == 1
        assert result.messages[0].content[0].type == "toolResult"
        assert result.messages[0].content[0].content == "file contents here"

    async def test_tool_result_extract_text(self) -> None:
        """ContentBlock.extract_text for toolResult returns '[Tool Result]'."""
        from app.models.session import ContentBlock
        block = ContentBlock(type="toolResult")
        assert block.extract_text() == "[Tool Result]"

    async def test_unknown_block_type_extract_text(self) -> None:
        """Unknown block type returns empty string from extract_text."""
        from app.models.session import ContentBlock
        block = ContentBlock(type="unknown_type")
        assert block.extract_text() == ""

    async def test_text_block_with_no_text_field(self) -> None:
        """Text block with text=None returns empty string."""
        from app.models.session import ContentBlock
        block = ContentBlock(type="text", text=None)
        assert block.extract_text() == ""

    async def test_thinking_block_with_no_thinking_field(self) -> None:
        """Thinking block with thinking=None returns empty string."""
        from app.models.session import ContentBlock
        block = ContentBlock(type="thinking", thinking=None)
        assert block.extract_text() == ""

    async def test_tool_call_block_with_no_name(self) -> None:
        """toolCall block without name returns empty string."""
        from app.models.session import ContentBlock
        block = ContentBlock(type="toolCall", name=None)
        assert block.extract_text() == ""


class TestSessionServiceEdgeCases:
    """Test edge cases: empty JSONL, corrupt JSON lines, non-dict entries."""

    async def test_empty_jsonl_file(self, tmp_path: Path) -> None:
        """Empty JSONL file returns zero messages."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {
                "sessionId": "s1",
                "updatedAt": 1000,
                "sessionFile": str(tmp_path / "sessions" / "s1.jsonl"),
            }
        })
        (tmp_path / "sessions" / "s1.jsonl").write_text("")
        svc = SessionService(settings=settings)
        result = await svc.get_messages("agent:main:main")
        assert result.total == 0
        assert result.messages == []
        assert result.has_more is False

    async def test_corrupt_json_lines_skipped(self, tmp_path: Path) -> None:
        """Lines with invalid JSON are skipped and counted."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {
                "sessionId": "s1",
                "updatedAt": 1000,
                "sessionFile": str(tmp_path / "sessions" / "s1.jsonl"),
            }
        })
        jsonl_path = tmp_path / "sessions" / "s1.jsonl"
        with open(jsonl_path, "w") as f:
            f.write("this is not json\n")
            f.write("{invalid json too\n")
            f.write(json.dumps({
                "type": "message", "id": "msg-1",
                "message": {"role": "user", "content": [{"type": "text", "text": "hello"}]},
            }) + "\n")
        svc = SessionService(settings=settings)
        result = await svc.get_messages("agent:main:main")
        assert result.total == 1
        assert result.skipped_lines == 2

    async def test_non_dict_jsonl_entries_skipped(self, tmp_path: Path) -> None:
        """JSONL entries that are not dicts (e.g., arrays, strings) are skipped."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {
                "sessionId": "s1",
                "updatedAt": 1000,
                "sessionFile": str(tmp_path / "sessions" / "s1.jsonl"),
            }
        })
        jsonl_path = tmp_path / "sessions" / "s1.jsonl"
        with open(jsonl_path, "w") as f:
            f.write('"just a string"\n')
            f.write("[1, 2, 3]\n")
            f.write("42\n")
            f.write(json.dumps({
                "type": "message", "id": "msg-1",
                "message": {"role": "user", "content": [{"type": "text", "text": "hi"}]},
            }) + "\n")
        svc = SessionService(settings=settings)
        result = await svc.get_messages("agent:main:main")
        assert result.total == 1
        assert result.skipped_lines == 3

    async def test_non_dict_raw_content_treated_as_empty(self, tmp_path: Path) -> None:
        """If message.content is not a list, it is treated as empty."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {
                "sessionId": "s1",
                "updatedAt": 1000,
                "sessionFile": str(tmp_path / "sessions" / "s1.jsonl"),
            }
        })
        _write_jsonl(tmp_path / "sessions" / "s1.jsonl", [
            {
                "type": "message", "id": "msg-1",
                "message": {"role": "user", "content": "not a list"},
            },
        ])
        svc = SessionService(settings=settings)
        result = await svc.get_messages("agent:main:main")
        assert result.total == 1
        assert result.messages[0].content_text == ""

    async def test_non_dict_msg_data_skipped(self, tmp_path: Path) -> None:
        """If message field is not a dict, the entry is silently skipped."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {
                "sessionId": "s1",
                "updatedAt": 1000,
                "sessionFile": str(tmp_path / "sessions" / "s1.jsonl"),
            }
        })
        _write_jsonl(tmp_path / "sessions" / "s1.jsonl", [
            {"type": "message", "id": "msg-1", "message": "not a dict"},
        ])
        svc = SessionService(settings=settings)
        result = await svc.get_messages("agent:main:main")
        # The message entry is counted in total but skipped during parsing
        assert result.total == 1
        assert len(result.messages) == 0

    async def test_non_dict_content_block_skipped(self, tmp_path: Path) -> None:
        """Non-dict items within the content list are skipped."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {
                "sessionId": "s1",
                "updatedAt": 1000,
                "sessionFile": str(tmp_path / "sessions" / "s1.jsonl"),
            }
        })
        _write_jsonl(tmp_path / "sessions" / "s1.jsonl", [
            {
                "type": "message", "id": "msg-1",
                "message": {
                    "role": "assistant",
                    "content": [
                        "just a string",
                        42,
                        {"type": "text", "text": "valid block"},
                    ],
                },
            },
        ])
        svc = SessionService(settings=settings)
        result = await svc.get_messages("agent:main:main", full=True)
        assert result.total == 1
        assert len(result.messages[0].content) == 1
        assert result.messages[0].content[0].text == "valid block"


class TestSessionServiceTruncation:
    """Test content text truncation in non-full mode."""

    async def test_content_truncated_at_2000_chars(self, tmp_path: Path) -> None:
        """Long content_text is truncated to 2000 chars + '...' when full=False."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {
                "sessionId": "s1",
                "updatedAt": 1000,
                "sessionFile": str(tmp_path / "sessions" / "s1.jsonl"),
            }
        })
        long_text = "A" * 5000
        _write_jsonl(tmp_path / "sessions" / "s1.jsonl", [
            {
                "type": "message", "id": "msg-1",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": long_text}],
                },
            },
        ])
        svc = SessionService(settings=settings)

        # Non-full mode: should be truncated
        result = await svc.get_messages("agent:main:main", full=False)
        assert len(result.messages[0].content_text) == 2003  # 2000 + "..."
        assert result.messages[0].content_text.endswith("...")

        # Full mode: should NOT be truncated
        result_full = await svc.get_messages("agent:main:main", full=True)
        assert len(result_full.messages[0].content_text) == 5000

    async def test_content_not_truncated_when_short(self, tmp_path: Path) -> None:
        """Short content_text is not truncated even in non-full mode."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {
                "sessionId": "s1",
                "updatedAt": 1000,
                "sessionFile": str(tmp_path / "sessions" / "s1.jsonl"),
            }
        })
        _write_jsonl(tmp_path / "sessions" / "s1.jsonl", [
            {
                "type": "message", "id": "msg-1",
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Short message"}],
                },
            },
        ])
        svc = SessionService(settings=settings)
        result = await svc.get_messages("agent:main:main", full=False)
        assert result.messages[0].content_text == "Short message"


class TestSessionServiceMissingSessions:
    """Test session listing with missing/deleted session files."""

    async def test_session_not_found_in_registry(self, tmp_path: Path) -> None:
        """Requesting messages for a nonexistent session key returns warning."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {"sessionId": "s1", "updatedAt": 1000},
        })
        svc = SessionService(settings=settings)
        result = await svc.get_messages("agent:nonexistent:session")
        assert result.total == 0
        assert "not found" in result.warning.lower()

    async def test_session_data_not_a_dict(self, tmp_path: Path) -> None:
        """If session data value is not a dict, return warning."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": "not a dict",
        })
        svc = SessionService(settings=settings)
        result = await svc.get_messages("agent:main:main")
        assert result.total == 0
        assert result.warning is not None

    async def test_session_no_session_file_field(self, tmp_path: Path) -> None:
        """If session entry lacks sessionFile, return warning."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {"sessionId": "s1", "updatedAt": 1000},
        })
        svc = SessionService(settings=settings)
        result = await svc.get_messages("agent:main:main")
        assert result.total == 0
        assert "no session file" in result.warning.lower()

    async def test_session_file_outside_home(self, tmp_path: Path) -> None:
        """Session file path outside OPENCLAW_HOME returns warning."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {
                "sessionId": "s1",
                "updatedAt": 1000,
                "sessionFile": "/etc/passwd",
            },
        })
        svc = SessionService(settings=settings)
        result = await svc.get_messages("agent:main:main")
        assert result.total == 0
        assert "outside" in result.warning.lower()


class TestSessionServiceCacheEdgeCases:
    """Test cache invalidation and edge cases."""

    async def test_corrupt_sessions_json_returns_none(self, tmp_path: Path) -> None:
        """Invalid JSON in sessions.json returns empty list."""
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "sessions.json").write_text("{invalid json")
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = SessionService(settings=settings)
        result = await svc.list_sessions("main")
        assert result.total == 0
        assert result.sessions == []

    async def test_whitespace_only_sessions_json(self, tmp_path: Path) -> None:
        """Whitespace-only sessions.json returns empty dict."""
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "sessions.json").write_text("   \n  \n  ")
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = SessionService(settings=settings)
        result = await svc.list_sessions("main")
        assert result.total == 0

    async def test_sessions_json_not_a_dict(self, tmp_path: Path) -> None:
        """sessions.json containing a list (not a dict) returns empty."""
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "sessions.json").write_text("[1, 2, 3]")
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = SessionService(settings=settings)
        result = await svc.list_sessions("main")
        assert result.total == 0

    async def test_invalidate_cache(self, tmp_path: Path) -> None:
        """invalidate_cache clears the internal cache."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {"sessionId": "s1", "updatedAt": 1000},
        })
        svc = SessionService(settings=settings)
        # Load cache
        await svc.list_sessions("main")
        assert svc._cache
        # Invalidate
        svc.invalidate_cache()
        assert svc._cache == {}
        assert svc._cache_mtime is None

    async def test_non_dict_session_value_skipped_in_listing(self, tmp_path: Path) -> None:
        """Non-dict values in sessions.json are skipped during listing."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": "string_not_dict",
            "agent:main:real": {"sessionId": "s2", "updatedAt": 2000},
        })
        svc = SessionService(settings=settings)
        result = await svc.list_sessions("main")
        assert result.total == 1
        assert result.sessions[0].session_id == "agent:main:real"


class TestSessionServiceBuildSummary:
    """Test _build_summary edge cases."""

    async def test_summary_with_origin_label(self, tmp_path: Path) -> None:
        """Label falls back to origin.label when label is missing."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:main": {
                "sessionId": "s1",
                "updatedAt": 1000,
                "origin": {"label": "from-origin"},
            },
        })
        svc = SessionService(settings=settings)
        result = await svc.list_sessions("main")
        assert result.total == 1
        assert result.sessions[0].label == "from-origin"

    async def test_summary_with_missing_updated_at(self, tmp_path: Path) -> None:
        """Missing updatedAt defaults to 0 and sorts last."""
        home, settings = _make_session_env(tmp_path, {
            "agent:main:early": {
                "sessionId": "s1",
                # No updatedAt field — defaults to 0
            },
            "agent:main:late": {
                "sessionId": "s2",
                "updatedAt": 9999,
            },
        })
        svc = SessionService(settings=settings)
        result = await svc.list_sessions("main")
        assert result.total == 2
        # The one with updatedAt=9999 should sort first (descending)
        assert result.sessions[0].session_id == "agent:main:late"
        assert result.sessions[1].updated_at == 0


# ===========================================================================
# GATEWAY SERVICE — uncovered lines
# ===========================================================================


class TestGatewayServiceStatus:
    """Test get_status paths: CLI not found, timeout, parse branches."""

    async def test_status_cli_not_found(self, tmp_path: Path) -> None:
        """get_status returns degraded when openclaw CLI is not in PATH."""
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = GatewayService(settings=settings)
        with patch("shutil.which", return_value=None):
            result = await svc.get_status()
        assert result.running is False
        assert "not found" in result.error.lower()

    async def test_status_timeout(self, tmp_path: Path) -> None:
        """get_status returns degraded on subprocess timeout."""
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = GatewayService(settings=settings)
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch.object(svc, "_run_cli", side_effect=TimeoutError("timed out")),
        ):
            result = await svc.get_status()
        assert result.running is False
        assert "timed out" in result.error.lower()

    async def test_status_generic_exception(self, tmp_path: Path) -> None:
        """get_status returns degraded on any unexpected exception."""
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = GatewayService(settings=settings)
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch.object(svc, "_run_cli", side_effect=OSError("connection refused")),
        ):
            result = await svc.get_status()
        assert result.running is False
        assert "CLI error" in result.error

    async def test_status_nonzero_return_code(self, tmp_path: Path) -> None:
        """Non-zero exit code from CLI means gateway not running."""
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = GatewayService(settings=settings)
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch.object(svc, "_run_cli", new_callable=AsyncMock, return_value=("", "not running", 1)),
        ):
            result = await svc.get_status()
        assert result.running is False
        assert "not running" in result.error.lower()

    async def test_status_nonzero_return_code_no_stderr(self, tmp_path: Path) -> None:
        """Non-zero exit with empty stderr shows exit code."""
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = GatewayService(settings=settings)
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch.object(svc, "_run_cli", new_callable=AsyncMock, return_value=("", "", 2)),
        ):
            result = await svc.get_status()
        assert result.running is False
        assert "Exit code 2" in result.error

    async def test_status_running_with_pid_and_uptime(self, tmp_path: Path) -> None:
        """Successful status parse extracts running, pid, uptime."""
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = GatewayService(settings=settings)
        stdout = "Gateway running\nPID: 12345\nUptime: 2h 30m"
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch.object(svc, "_run_cli", new_callable=AsyncMock, return_value=(stdout, "", 0)),
        ):
            result = await svc.get_status()
        assert result.running is True
        assert result.pid == 12345
        assert result.uptime == "2h 30m"
        assert result.error is None


class TestGatewayParsingHelpers:
    """Test the module-level parsing helper functions directly."""

    def test_detect_running_with_running_keyword(self) -> None:
        assert _detect_running("Gateway is running on port 3000") is True

    def test_detect_running_with_not_running(self) -> None:
        assert _detect_running("Gateway is not running") is False

    def test_detect_running_with_started(self) -> None:
        assert _detect_running("Gateway started successfully") is True

    def test_detect_running_with_online(self) -> None:
        assert _detect_running("Status: online") is True

    def test_detect_running_with_no_keywords(self) -> None:
        assert _detect_running("Some random output") is False

    def test_extract_pid_found(self) -> None:
        assert _extract_pid("Process PID: 42069") == 42069

    def test_extract_pid_not_found(self) -> None:
        assert _extract_pid("No process info here") is None

    def test_extract_pid_various_formats(self) -> None:
        assert _extract_pid("pid 99999") == 99999
        assert _extract_pid("PID:12345") == 12345

    def test_extract_uptime_found(self) -> None:
        assert _extract_uptime("Uptime: 5h 12m") == "5h 12m"

    def test_extract_uptime_not_found(self) -> None:
        assert _extract_uptime("No time info here") is None

    def test_extract_channels_returns_empty(self) -> None:
        assert _extract_channels("anything") == {}


class TestGatewayServiceRunCommand:
    """Test run_command paths: CLI not found, timeout, success/failure."""

    async def test_run_command_cli_not_found(self, tmp_path: Path) -> None:
        """run_command raises FileNotFoundError when CLI not in PATH."""
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = GatewayService(settings=settings)
        with patch("shutil.which", return_value=None):
            with pytest.raises(FileNotFoundError):
                await svc.run_command(GatewayAction.START)

    async def test_run_command_timeout(self, tmp_path: Path) -> None:
        """run_command raises TimeoutError on subprocess timeout."""
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = GatewayService(settings=settings)
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch.object(svc, "_run_cli", side_effect=TimeoutError("timed out")),
        ):
            with pytest.raises(TimeoutError):
                await svc.run_command(GatewayAction.RESTART)

    async def test_run_command_success(self, tmp_path: Path) -> None:
        """Successful command returns success=True and records history."""
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = GatewayService(settings=settings)
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch.object(
                svc, "_run_cli", new_callable=AsyncMock,
                return_value=("Gateway started.", "", 0),
            ),
        ):
            result = await svc.run_command(GatewayAction.START)
        assert result.success is True
        assert result.action == GatewayAction.START
        assert "succeeded" in result.message
        # Check history was recorded
        history = svc.get_history()
        assert history.total == 1
        assert history.commands[0].command == "start"
        assert history.commands[0].exit_code == 0

    async def test_run_command_failure(self, tmp_path: Path) -> None:
        """Failed command returns success=False."""
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = GatewayService(settings=settings)
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch.object(
                svc, "_run_cli", new_callable=AsyncMock,
                return_value=("", "Error: already stopped", 1),
            ),
        ):
            result = await svc.run_command(GatewayAction.STOP)
        assert result.success is False
        assert "failed" in result.message

    async def test_run_command_output_truncated(self, tmp_path: Path) -> None:
        """Command output in history is truncated to 500 chars."""
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = GatewayService(settings=settings)
        long_output = "x" * 1000
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch.object(
                svc, "_run_cli", new_callable=AsyncMock,
                return_value=(long_output, "", 0),
            ),
        ):
            await svc.run_command(GatewayAction.START)
        history = svc.get_history()
        assert len(history.commands[0].output) == 500


class TestGatewayServiceIsInstalled:
    """Test is_installed method."""

    def test_is_installed_true(self, tmp_path: Path) -> None:
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = GatewayService(settings=settings)
        with patch("shutil.which", return_value="/usr/bin/openclaw"):
            assert svc.is_installed() is True

    def test_is_installed_false(self, tmp_path: Path) -> None:
        settings = Settings(OPENCLAW_HOME=tmp_path)
        svc = GatewayService(settings=settings)
        with patch("shutil.which", return_value=None):
            assert svc.is_installed() is False


# ===========================================================================
# ROUTERS / SESSIONS — uncovered lines
# ===========================================================================


class TestSessionMessagesEndpoint:
    """Test GET /api/sessions/{session_id}/messages via HTTP."""

    async def test_get_messages_valid_session(
        self, async_client, mock_openclaw_home: Path,
    ) -> None:
        """GET messages for a valid session returns 200."""
        sessions_dir = mock_openclaw_home / "sessions"
        jsonl_path = sessions_dir / "session-001.jsonl"
        _write_jsonl(jsonl_path, [
            {
                "type": "message", "id": "msg-1",
                "timestamp": "2026-01-01T00:00:00Z",
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Hello"}],
                },
            },
        ])
        sessions_json = sessions_dir / "sessions.json"
        data = json.loads(sessions_json.read_text())
        data["agent:main:main"]["sessionFile"] = str(jsonl_path)
        sessions_json.write_text(json.dumps(data))

        response = await async_client.get("/api/sessions/agent:main:main/messages")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["messages"][0]["role"] == "user"

    async def test_get_messages_invalid_session(self, async_client) -> None:
        """GET messages for a nonexistent session returns 200 with warning."""
        response = await async_client.get("/api/sessions/agent:nobody:nowhere/messages")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 0
        assert body["warning"] is not None

    async def test_get_messages_path_traversal(self, async_client) -> None:
        """Path traversal in session_id returns 403."""
        response = await async_client.get(
            "/api/sessions/%2e%2e%2fetc%2fpasswd/messages"
        )
        assert response.status_code == 403

    async def test_get_messages_with_pagination(
        self, async_client, mock_openclaw_home: Path,
    ) -> None:
        """Pagination query params work through the endpoint."""
        sessions_dir = mock_openclaw_home / "sessions"
        jsonl_path = sessions_dir / "session-001.jsonl"
        entries = []
        for i in range(5):
            entries.append({
                "type": "message", "id": f"msg-{i}",
                "message": {"role": "user", "content": [{"type": "text", "text": f"Msg {i}"}]},
            })
        _write_jsonl(jsonl_path, entries)
        sessions_json = sessions_dir / "sessions.json"
        data = json.loads(sessions_json.read_text())
        data["agent:main:main"]["sessionFile"] = str(jsonl_path)
        sessions_json.write_text(json.dumps(data))

        response = await async_client.get(
            "/api/sessions/agent:main:main/messages?limit=2&offset=0"
        )
        body = response.json()
        assert body["total"] == 5
        assert len(body["messages"]) == 2
        assert body["has_more"] is True

    async def test_get_messages_full_mode(
        self, async_client, mock_openclaw_home: Path,
    ) -> None:
        """Full mode includes content blocks."""
        sessions_dir = mock_openclaw_home / "sessions"
        jsonl_path = sessions_dir / "session-001.jsonl"
        _write_jsonl(jsonl_path, [
            {
                "type": "message", "id": "msg-1",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "thinking", "thinking": "hmm"},
                        {"type": "text", "text": "hello"},
                    ],
                },
            },
        ])
        sessions_json = sessions_dir / "sessions.json"
        data = json.loads(sessions_json.read_text())
        data["agent:main:main"]["sessionFile"] = str(jsonl_path)
        sessions_json.write_text(json.dumps(data))

        response = await async_client.get(
            "/api/sessions/agent:main:main/messages?full=true"
        )
        body = response.json()
        assert len(body["messages"][0]["content"]) == 2


class TestSessionListEndpoint:
    """Test GET /api/agents/{agent_id}/sessions via HTTP."""

    async def test_list_sessions_endpoint(self, async_client) -> None:
        """GET /api/agents/main/sessions returns 200."""
        response = await async_client.get("/api/agents/main/sessions")
        assert response.status_code == 200
        body = response.json()
        assert "sessions" in body
        assert "total" in body

    async def test_list_sessions_for_unknown_agent(self, async_client) -> None:
        """GET sessions for agent with no sessions returns empty list."""
        response = await async_client.get("/api/agents/nonexistent/sessions")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 0
        assert body["sessions"] == []


# ===========================================================================
# ROUTERS / HEALTH — uncovered lines
# ===========================================================================


class TestHealthEndpoint:
    """Test health endpoint with various subsystem states."""

    async def test_health_ok(self, async_client) -> None:
        """Health returns 200 with status field."""
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] in ("ok", "degraded")
        assert "subsystems" in body
        assert "version" in body

    async def test_health_degraded_no_config(
        self, async_client, mock_openclaw_home: Path,
    ) -> None:
        """Health is degraded when openclaw.json is missing."""
        config_path = mock_openclaw_home / "openclaw.json"
        config_path.unlink()
        response = await async_client.get("/api/health")
        body = response.json()
        assert body["status"] == "degraded"
        assert body["subsystems"]["config"] is False

    async def test_health_degraded_empty_config(
        self, async_client, mock_openclaw_home: Path,
    ) -> None:
        """Health is degraded when openclaw.json is empty (0 bytes)."""
        config_path = mock_openclaw_home / "openclaw.json"
        config_path.write_text("")
        response = await async_client.get("/api/health")
        body = response.json()
        assert body["subsystems"]["config"] is False

    async def test_health_degraded_no_workspace(
        self, async_client, mock_openclaw_home: Path,
    ) -> None:
        """Health is degraded when workspace directory is missing."""
        import shutil
        shutil.rmtree(mock_openclaw_home / "workspace")
        response = await async_client.get("/api/health")
        body = response.json()
        assert body["subsystems"]["workspaces"] is False

    async def test_health_gateway_cli_subsystem(self, async_client) -> None:
        """Gateway CLI subsystem reflects whether openclaw is in PATH."""
        # In test environment, openclaw is likely not in PATH
        response = await async_client.get("/api/health")
        body = response.json()
        # Just verify the key exists and is a bool
        assert isinstance(body["subsystems"]["gateway_cli"], bool)

    async def test_health_sessions_subsystem(self, async_client) -> None:
        """Sessions subsystem reflects whether sessions dir exists."""
        response = await async_client.get("/api/health")
        body = response.json()
        assert body["subsystems"]["sessions"] is True

    async def test_health_degraded_no_sessions_dir(
        self, async_client, mock_openclaw_home: Path,
    ) -> None:
        """Health sessions is False when sessions dir is missing."""
        import shutil
        shutil.rmtree(mock_openclaw_home / "sessions")
        response = await async_client.get("/api/health")
        body = response.json()
        assert body["subsystems"]["sessions"] is False


# ===========================================================================
# FILE SERVICE — uncovered lines
# ===========================================================================


class TestFileServiceWrite:
    """Test write_file: directory creation, ETag mismatch, new file."""

    async def test_write_creates_parent_directories(
        self, file_service: FileService, mock_openclaw_home: Path,
    ) -> None:
        """write_file creates parent directories that do not exist."""
        target = mock_openclaw_home / "workspace" / "subdir" / "deep" / "file.md"
        etag = await file_service.write_file(target, "# Hello", if_match=None)
        assert target.exists()
        assert target.read_text() == "# Hello"
        assert etag  # non-empty string

    async def test_write_etag_mismatch_raises(
        self, file_service: FileService, mock_openclaw_home: Path,
    ) -> None:
        """write_file with wrong if_match raises ETagMismatchError."""
        target = mock_openclaw_home / "workspace" / "etag_test.md"
        await file_service.write_file(target, "original", if_match=None)
        with pytest.raises(ETagMismatchError) as exc_info:
            await file_service.write_file(target, "changed", if_match="wrong_etag")
        assert exc_info.value.current_etag  # should have the real etag

    async def test_write_etag_match_succeeds(
        self, file_service: FileService, mock_openclaw_home: Path,
    ) -> None:
        """write_file with correct if_match succeeds."""
        target = mock_openclaw_home / "workspace" / "etag_ok.md"
        etag = await file_service.write_file(target, "v1", if_match=None)
        new_etag = await file_service.write_file(target, "v2", if_match=etag)
        assert new_etag != etag
        assert target.read_text() == "v2"

    async def test_write_new_file_no_etag_check(
        self, file_service: FileService, mock_openclaw_home: Path,
    ) -> None:
        """write_file with if_match on a new (nonexistent) file skips ETag check."""
        target = mock_openclaw_home / "workspace" / "brand_new.md"
        etag = await file_service.write_file(target, "content", if_match="any_etag")
        assert target.exists()
        assert etag


class TestFileServiceRead:
    """Test read_file edge cases."""

    async def test_read_nonexistent_raises(
        self, file_service: FileService, mock_openclaw_home: Path,
    ) -> None:
        """read_file raises FileNotFoundError for missing file."""
        target = mock_openclaw_home / "workspace" / "nope.md"
        with pytest.raises(FileNotFoundError):
            await file_service.read_file(target)

    async def test_read_directory_raises(
        self, file_service: FileService, mock_openclaw_home: Path,
    ) -> None:
        """read_file raises FileNotFoundError for a directory."""
        target = mock_openclaw_home / "workspace"
        with pytest.raises(FileNotFoundError, match="Not a file"):
            await file_service.read_file(target)

    async def test_read_outside_sandbox_raises(
        self, file_service: FileService,
    ) -> None:
        """read_file raises PermissionError for path outside sandbox."""
        with pytest.raises(PermissionError):
            await file_service.read_file(Path("/etc/passwd"))


class TestFileServiceMisc:
    """Test compute_etag, get_mtime, detect_language."""

    def test_compute_etag(
        self, file_service: FileService, mock_openclaw_home: Path,
    ) -> None:
        """compute_etag returns a 16-char hex hash."""
        target = mock_openclaw_home / "workspace" / "AGENTS.md"
        etag = file_service.compute_etag(target)
        assert len(etag) == 16
        assert all(c in "0123456789abcdef" for c in etag)

    def test_get_mtime(
        self, file_service: FileService, mock_openclaw_home: Path,
    ) -> None:
        """get_mtime returns a timezone-aware datetime."""
        from datetime import timezone
        target = mock_openclaw_home / "workspace" / "AGENTS.md"
        mtime = file_service.get_mtime(target)
        assert mtime.tzinfo == timezone.utc

    def test_detect_language_various_extensions(self, file_service: FileService) -> None:
        """detect_language covers additional extensions."""
        assert file_service.detect_language("test.tsx") == "typescriptreact"
        assert file_service.detect_language("test.jsx") == "javascriptreact"
        assert file_service.detect_language("test.toml") == "toml"
        assert file_service.detect_language("test.css") == "css"
        assert file_service.detect_language("test.html") == "html"
        assert file_service.detect_language("test.xml") == "xml"
        assert file_service.detect_language("test.sql") == "sql"
        assert file_service.detect_language("test.env") == "plaintext"
        assert file_service.detect_language("test.bash") == "shell"
        assert file_service.detect_language("test.zsh") == "shell"

    def test_check_path_write_outside_sandbox(
        self, file_service: FileService,
    ) -> None:
        """_check_path with write=True outside sandbox raises PermissionError."""
        with pytest.raises(PermissionError):
            file_service._check_path(Path("/tmp/evil.txt"), write=True)


# ===========================================================================
# CONFIG SERVICE — uncovered lines
# ===========================================================================


class TestConfigServiceBackup:
    """Test backup creation and pruning."""

    async def test_backup_created_on_write(
        self, config_service: ConfigService, mock_openclaw_home: Path,
    ) -> None:
        """Writing config creates a backup file."""
        from app.models.config import ConfigWriteRequest
        # Read current config
        resp = await config_service.read_config()
        # Write it back
        request = ConfigWriteRequest(config=resp.config, etag=resp.etag)
        await config_service.write_config(request)
        backups = list(mock_openclaw_home.glob("openclaw.json.bak.*"))
        assert len(backups) >= 1

    async def test_backup_pruning(
        self, config_service: ConfigService, mock_openclaw_home: Path,
    ) -> None:
        """After many writes, only 10 backups remain."""
        from app.models.config import ConfigWriteRequest
        import time

        for i in range(12):
            resp = await config_service.read_config()
            config = resp.config
            config["iteration"] = i
            request = ConfigWriteRequest(config=config, etag=None)
            await config_service.write_config(request)
            # Tiny sleep to ensure unique timestamps
            time.sleep(0.01)

        backups = list(mock_openclaw_home.glob("openclaw.json.bak.*"))
        assert len(backups) <= 10

    async def test_backup_not_created_for_new_file(
        self, tmp_path: Path,
    ) -> None:
        """No backup is created when config file does not exist yet."""
        from app.models.config import ConfigWriteRequest
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        settings = Settings(OPENCLAW_HOME=tmp_path)
        fs = FileService(settings=settings)
        svc = ConfigService(settings=settings, file_service=fs)

        request = ConfigWriteRequest(config={"agents": {}}, etag=None)
        await svc.write_config(request)
        backups = list(tmp_path.glob("openclaw.json.bak.*"))
        assert len(backups) == 0


class TestConfigServiceWriteEdgeCases:
    """Test write_config edge cases."""

    async def test_write_config_without_etag(
        self, config_service: ConfigService, mock_openclaw_home: Path,
    ) -> None:
        """write_config without etag skips ETag check."""
        from app.models.config import ConfigWriteRequest
        request = ConfigWriteRequest(config={"agents": {}}, etag=None)
        result = await config_service.write_config(request)
        assert result.etag
        assert result.config == {"agents": {}}

    async def test_write_config_etag_mismatch(
        self, config_service: ConfigService,
    ) -> None:
        """write_config with wrong etag raises ETagMismatchError."""
        from app.models.config import ConfigWriteRequest
        request = ConfigWriteRequest(config={"agents": {}}, etag="wrong_etag")
        with pytest.raises(ETagMismatchError):
            await config_service.write_config(request)

    async def test_write_config_with_corrupt_existing_json(
        self, mock_openclaw_home: Path,
    ) -> None:
        """write_config handles corrupt existing openclaw.json gracefully."""
        from app.models.config import ConfigWriteRequest
        config_path = mock_openclaw_home / "openclaw.json"
        config_path.write_text("{not valid json")
        settings = Settings(OPENCLAW_HOME=mock_openclaw_home)
        fs = FileService(settings=settings)
        svc = ConfigService(settings=settings, file_service=fs)
        request = ConfigWriteRequest(config={"agents": {}}, etag=None)
        result = await svc.write_config(request)
        assert result.etag
        # Verify it was written correctly
        on_disk = json.loads(config_path.read_text())
        assert on_disk == {"agents": {}}


class TestConfigServiceValidateEdgeCases:
    """Test validate_config edge cases."""

    async def test_validate_with_nonexistent_workspace_warns(
        self, config_service: ConfigService,
    ) -> None:
        """Validation warns when workspace path does not exist."""
        config = {
            "agents": {
                "defaults": {
                    "workspace": "/nonexistent/path/that/does/not/exist",
                },
            },
        }
        result = await config_service.validate_config(config)
        assert result.valid is True  # warning, not error
        assert len(result.warnings) > 0
        assert "does not exist" in result.warnings[0]

    async def test_validate_with_string_port_returns_error(
        self, config_service: ConfigService,
    ) -> None:
        """Non-integer gateway port returns validation error."""
        config = {"gateway": {"port": "not-a-number"}}
        result = await config_service.validate_config(config)
        assert result.valid is False
        assert any("port" in e.lower() for e in result.errors)

    async def test_validate_with_port_too_high(
        self, config_service: ConfigService,
    ) -> None:
        """Port above 65535 returns validation error."""
        config = {"gateway": {"port": 70000}}
        result = await config_service.validate_config(config)
        assert result.valid is False


class TestConfigServiceRestoreRedacted:
    """Test _restore_redacted edge cases."""

    def test_restore_redacted_nested(self) -> None:
        """Nested __REDACTED__ values restored from original."""
        incoming = {"api": {"key": "__REDACTED__", "name": "test"}}
        original = {"api": {"key": "real-secret", "name": "old-name"}}
        result = _restore_redacted(incoming, original)
        assert result["api"]["key"] == "real-secret"
        assert result["api"]["name"] == "test"

    def test_restore_redacted_missing_key_in_original(self) -> None:
        """__REDACTED__ value with no original keeps __REDACTED__."""
        incoming = {"new_secret": "__REDACTED__"}
        original = {}
        result = _restore_redacted(incoming, original)
        assert result["new_secret"] == "__REDACTED__"

    def test_redact_secrets_empty_string_not_redacted(self) -> None:
        """Empty string values for secret keys are NOT redacted."""
        result = _redact_secrets({"api_key": ""})
        assert result["api_key"] == ""

    def test_redact_secrets_integer_not_redacted(self) -> None:
        """Integer values for secret-named keys are NOT redacted."""
        result = _redact_secrets({"token_count": 42})
        assert result["token_count"] == 42


# ===========================================================================
# GATEWAY ROUTER — endpoint tests
# ===========================================================================


class TestGatewayStatusEndpoint:
    """Test GET /api/gateway/status via HTTP."""

    async def test_gateway_status_endpoint(self, async_client) -> None:
        """GET /api/gateway/status returns 200."""
        with patch("shutil.which", return_value=None):
            response = await async_client.get("/api/gateway/status")
        assert response.status_code == 200
        body = response.json()
        assert "running" in body

    async def test_gateway_status_not_installed(self, async_client) -> None:
        """Gateway status shows error when CLI not installed."""
        with patch("shutil.which", return_value=None):
            response = await async_client.get("/api/gateway/status")
        body = response.json()
        assert body["running"] is False
        assert "not found" in body["error"].lower()


class TestGatewayCommandEndpoint:
    """Test POST /api/gateway/{action} via HTTP."""

    async def test_gateway_start_cli_not_found(self, async_client) -> None:
        """POST /api/gateway/start with no CLI returns 404."""
        with patch("shutil.which", return_value=None):
            response = await async_client.post("/api/gateway/start")
        assert response.status_code == 404

    async def test_gateway_start_success(self, async_client) -> None:
        """POST /api/gateway/start with mocked CLI returns 200."""
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "app.services.gateway_service.GatewayService._run_cli",
                new_callable=AsyncMock,
                return_value=("Gateway started.", "", 0),
            ),
        ):
            response = await async_client.post("/api/gateway/start")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True

    async def test_gateway_invalid_action_returns_422(self, async_client) -> None:
        """POST /api/gateway/invalid returns 422 (enum validation)."""
        response = await async_client.post("/api/gateway/invalid_action")
        assert response.status_code == 422

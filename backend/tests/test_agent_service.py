"""Tests for AgentService internal methods.

Covers:
  - _last_activity() with real session key format (agent:main:main)
  - _last_activity() with ms Unix timestamps
  - _last_activity() with no matching sessions
  - _discover_agent_ids() scans OPENCLAW_HOME not home parent
  - _list_workspace_files() filters against WORKSPACE_FILES set
  - _extract_agent_meta() session model fallback
  - now_iso() utility function
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.services.agent_service import AgentService


class TestLastActivity:
    """Tests for AgentService._last_activity()."""

    def test_last_activity_real_key_format(self, agent_service: AgentService):
        """Sessions with keys like agent:main:main return correct timestamp."""
        sessions = {
            "agent:main:main": {
                "sessionId": "session-001",
                "updatedAt": 1772031239308,
            },
            "agent:main:subagent:abc": {
                "sessionId": "session-002",
                "updatedAt": 1772031200000,
            },
            "agent:coder:main": {
                "sessionId": "session-003",
                "updatedAt": 1772090000000,
            },
        }
        result = agent_service._last_activity("main", sessions)
        assert result is not None
        # Should return the most recent one (1772031239308 > 1772031200000)
        expected = datetime.fromtimestamp(1772031239308 / 1000, tz=UTC)
        assert result == expected

    def test_last_activity_ms_timestamp(self, agent_service: AgentService):
        """updatedAt as int (ms) is parsed correctly."""
        sessions = {
            "agent:test:main": {
                "updatedAt": 1700000000000,  # Nov 14, 2023
            },
        }
        result = agent_service._last_activity("test", sessions)
        assert result is not None
        expected = datetime.fromtimestamp(1700000000, tz=UTC)
        assert result == expected

    def test_last_activity_no_matching_sessions(self, agent_service: AgentService):
        """Agent with no sessions returns None."""
        sessions = {
            "agent:coder:main": {
                "updatedAt": 1772031239308,
            },
        }
        result = agent_service._last_activity("nonexistent", sessions)
        assert result is None

    def test_last_activity_empty_sessions(self, agent_service: AgentService):
        """Empty sessions dict returns None."""
        result = agent_service._last_activity("main", {})
        assert result is None


class TestDiscoverAgentIds:
    """Tests for AgentService._discover_agent_ids()."""

    @pytest.mark.asyncio
    async def test_discover_agents_scans_openclaw_home(
        self, agent_service: AgentService, mock_openclaw_home: Path
    ):
        """workspace-* dirs are discovered from OPENCLAW_HOME, not parent."""
        ids = await agent_service._discover_agent_ids()
        # Should find "main" (hardcoded) and "coder" (from workspace-coder)
        assert "main" in ids
        assert "coder" in ids

    @pytest.mark.asyncio
    async def test_discover_agents_ignores_parent_workspace_dirs(
        self, mock_openclaw_home: Path, test_settings, file_service
    ):
        """workspace-* dirs in OPENCLAW_HOME parent are NOT discovered."""
        # Create a workspace-fake directory in the PARENT of OPENCLAW_HOME
        fake_ws = mock_openclaw_home.parent / "workspace-fake"
        fake_ws.mkdir()

        svc = AgentService(settings=test_settings, file_service=file_service)
        ids = await svc._discover_agent_ids()
        assert "fake" not in ids


class TestListWorkspaceFiles:
    """Tests for _list_workspace_files filtering against WORKSPACE_FILES."""

    @pytest.mark.asyncio
    async def test_workspace_files_filtered(
        self, agent_service: AgentService, mock_openclaw_home: Path
    ):
        """Only files in WORKSPACE_FILES set are returned."""
        workspace = mock_openclaw_home / "workspace"
        # Create a file NOT in WORKSPACE_FILES
        (workspace / "random_notes.txt").write_text("not a workspace file")
        (workspace / ".hidden").write_text("hidden file")

        files = await agent_service._list_workspace_files(workspace)
        names = [f.name for f in files]

        # Should include known workspace files
        assert "AGENTS.md" in names
        assert "SOUL.md" in names

        # Should NOT include unknown files
        assert "random_notes.txt" not in names
        assert ".hidden" not in names


class TestExtractAgentMeta:
    """Tests for _extract_agent_meta() with session model fallback."""

    def test_agent_model_from_session(self, agent_service: AgentService):
        """Agent with session returns session model, not config default."""
        cfg = {
            "agents": {
                "defaults": {"model": {"primary": "openai-codex/gpt-5.3-codex"}},
            }
        }
        sessions = {
            "agent:main:main": {
                "updatedAt": 1772031239308,
                "model": "claude-opus-4-6",
            },
        }
        name, model = agent_service._extract_agent_meta("main", cfg, sessions)
        assert model == "claude-opus-4-6"

    def test_agent_model_falls_back_to_config(self, agent_service: AgentService):
        """Agent without sessions returns config default model."""
        cfg = {
            "agents": {
                "defaults": {"model": {"primary": "openai-codex/gpt-5.3-codex"}},
            }
        }
        sessions = {}
        name, model = agent_service._extract_agent_meta("main", cfg, sessions)
        assert model == "openai-codex/gpt-5.3-codex"

    def test_agent_model_no_sessions_arg(self, agent_service: AgentService):
        """Without sessions arg, falls back to config model."""
        cfg = {
            "agents": {
                "defaults": {"model": "some-model"},
            }
        }
        name, model = agent_service._extract_agent_meta("main", cfg)
        assert model == "some-model"


class TestNowIso:
    """Test for extracted now_iso utility."""

    def test_now_iso_returns_iso_string(self):
        """now_iso returns a valid ISO 8601 string."""
        from app.utils import now_iso

        result = now_iso()
        # Should be parseable as a datetime
        parsed = datetime.fromisoformat(result)
        assert parsed.tzinfo is not None


class TestListWorkspaceFilesRecursive:
    """Tests for list_workspace_files_recursive."""

    @pytest.mark.asyncio
    async def test_recursive_listing(
        self, agent_service: AgentService, mock_openclaw_home: Path
    ):
        """Returns files from subdirectories when recursive=True."""
        workspace = mock_openclaw_home / "workspace"
        # Create a subdirectory with a file
        subdir = workspace / "memory"
        subdir.mkdir(exist_ok=True)
        (subdir / "notes.md").write_text("# Notes")

        result = await agent_service.list_workspace_files_recursive(
            "main",
            recursive=True,
            depth=2,
            max_files=200,
        )
        paths = [f.path for f in result.files]
        assert "memory/notes.md" in paths
        assert result.truncated is False

    @pytest.mark.asyncio
    async def test_depth_limit(
        self, agent_service: AgentService, mock_openclaw_home: Path
    ):
        """Max depth 3 enforced — files beyond depth 3 not returned."""
        workspace = mock_openclaw_home / "workspace"
        # Create nested dirs: level1/level2/level3/level4
        deep = workspace / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        (deep / "deep.txt").write_text("deep file")
        # Also create a file at depth 3 (should be included)
        (workspace / "a" / "b" / "c" / "shallow.txt").write_text("shallow")

        result = await agent_service.list_workspace_files_recursive(
            "main",
            recursive=True,
            depth=3,
            max_files=200,
        )
        paths = [f.path for f in result.files]
        # depth=3 means we can go 3 levels deep: a/b/c is ok, a/b/c/d is not
        assert "a/b/c/shallow.txt" in paths
        assert "a/b/c/d/deep.txt" not in paths

    @pytest.mark.asyncio
    async def test_excludes(
        self, agent_service: AgentService, mock_openclaw_home: Path
    ):
        """.git, node_modules, __pycache__ directories are excluded."""
        workspace = mock_openclaw_home / "workspace"
        (workspace / ".git").mkdir(exist_ok=True)
        (workspace / ".git" / "config").write_text("git config")
        (workspace / "node_modules").mkdir(exist_ok=True)
        (workspace / "node_modules" / "package.json").write_text("{}")
        (workspace / "__pycache__").mkdir(exist_ok=True)
        (workspace / "__pycache__" / "mod.cpython-311.pyc").write_bytes(b"\x00")

        result = await agent_service.list_workspace_files_recursive(
            "main",
            recursive=True,
            depth=2,
            max_files=200,
        )
        paths = [f.path for f in result.files]
        assert not any(".git" in p for p in paths)
        assert not any("node_modules" in p for p in paths)
        assert not any("__pycache__" in p for p in paths)

    @pytest.mark.asyncio
    async def test_max_files_truncation(
        self, agent_service: AgentService, mock_openclaw_home: Path
    ):
        """>max_files returns truncated=True."""
        workspace = mock_openclaw_home / "workspace"
        # Create 10 files, set max to 5
        for i in range(10):
            (workspace / f"file_{i:02d}.txt").write_text(f"content {i}")

        result = await agent_service.list_workspace_files_recursive(
            "main",
            recursive=False,
            max_files=5,
        )
        assert len(result.files) == 5
        assert result.truncated is True

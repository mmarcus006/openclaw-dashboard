"""Shared pytest fixtures for OpenClaw Dashboard backend tests.

IMPORTANT: All tests MUST use mock_openclaw_home — never touch the real ~/.openclaw/.
The fixture injects a temporary directory and overrides FastAPI dependencies so that
no file operations touch the real filesystem.
"""

import json
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import create_app
from app.services.agent_service import AgentService
from app.services.config_service import ConfigService
from app.services.cron_service import CronService
from app.services.file_service import FileService
from app.services.gateway_service import GatewayService
from app.services.session_service import SessionService

# ---------------------------------------------------------------------------
# Core mock home fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_openclaw_home(tmp_path: Path) -> Path:
    """Create a realistic ~/.openclaw/ structure in a temp dir.

    Structure:
        tmp_path/
        ├── workspace/          # main agent workspace
        │   ├── AGENTS.md
        │   ├── SOUL.md
        │   ├── MEMORY.md
        │   └── ACTIVE.md
        ├── workspace-coder/    # coder agent workspace
        │   ├── AGENTS.md
        │   └── SOUL.md
        ├── agents/
        │   └── coder/          # agent config dir (empty)
        ├── openclaw.json       # valid config
        └── sessions/
            └── sessions.json   # minimal sessions data

    Returns:
        Path to the temporary openclaw home directory.
    """
    # Main workspace
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "AGENTS.md").write_text("# AGENTS.md - Your Workspace\nThis is the agents file.")
    (workspace / "SOUL.md").write_text("# SOUL.md - Who You Are\nYou are COS.")
    (workspace / "MEMORY.md").write_text("# MEMORY.md\nLong-term memory.")
    (workspace / "ACTIVE.md").write_text("# ACTIVE.md\nActive tasks.")

    # Coder workspace
    coder_ws = tmp_path / "workspace-coder"
    coder_ws.mkdir()
    (coder_ws / "AGENTS.md").write_text("# Coder AGENTS.md")
    (coder_ws / "SOUL.md").write_text("# Coder SOUL.md")

    # Agent config dirs
    agents_dir = tmp_path / "agents" / "coder"
    agents_dir.mkdir(parents=True)

    # openclaw.json
    config = {
        "agents": {
            "defaults": {
                "model": "anthropic/claude-sonnet-4-6",
                "workspace": str(workspace),
            },
            "coder": {
                "name": "Coder Agent",
                "model": "anthropic/claude-sonnet-4-6",
            },
        },
        "gateway": {
            "port": 3000,
        },
        "api": {
            "openai_api_key": "sk-test-secret-key",
            "anthropic_token": "ant-test-token",
        },
    }
    (tmp_path / "openclaw.json").write_text(json.dumps(config, indent=2))

    # Sessions — use real sessions.json format (keys are session keys, updatedAt is ms)
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    sessions_data = {
        "agent:main:main": {
            "sessionId": "session-001",
            "updatedAt": 1772031239308,
            "model": "claude-opus-4-6",
            "modelProvider": "anthropic",
            "totalTokens": 5000,
            "inputTokens": 2000,
            "outputTokens": 3000,
        },
        "agent:coder:main": {
            "sessionId": "session-002",
            "updatedAt": 1772020000000,
            "model": "claude-sonnet-4-6",
            "modelProvider": "anthropic",
        },
    }
    (sessions_dir / "sessions.json").write_text(json.dumps(sessions_data))

    return tmp_path


# ---------------------------------------------------------------------------
# Settings / service fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_settings(mock_openclaw_home: Path) -> Settings:
    """Return Settings pointed at the mock openclaw home.

    Args:
        mock_openclaw_home: Path to the temp directory.

    Returns:
        Settings instance with OPENCLAW_HOME set to the temp dir.
    """
    return Settings(OPENCLAW_HOME=mock_openclaw_home)


@pytest.fixture
def file_service(test_settings: Settings) -> FileService:
    """Return a FileService using the mock home.

    Args:
        test_settings: Test settings pointing to temp dir.

    Returns:
        FileService instance.
    """
    return FileService(settings=test_settings)


@pytest.fixture
def agent_service(test_settings: Settings, file_service: FileService) -> AgentService:
    """Return an AgentService using the mock home.

    Args:
        test_settings: Test settings pointing to temp dir.
        file_service: FileService pointing to temp dir.

    Returns:
        AgentService instance.
    """
    return AgentService(settings=test_settings, file_service=file_service)


@pytest.fixture
def config_service(test_settings: Settings, file_service: FileService) -> ConfigService:
    """Return a ConfigService using the mock home.

    Args:
        test_settings: Test settings pointing to temp dir.
        file_service: FileService pointing to temp dir.

    Returns:
        ConfigService instance.
    """
    return ConfigService(settings=test_settings, file_service=file_service)


@pytest.fixture
def gateway_service(test_settings: Settings) -> GatewayService:
    """Return a GatewayService using the mock home.

    Args:
        test_settings: Test settings pointing to temp dir.

    Returns:
        GatewayService instance.
    """
    return GatewayService(settings=test_settings)


@pytest.fixture
def session_service(test_settings: Settings) -> SessionService:
    """Return a SessionService using the mock home.

    Args:
        test_settings: Test settings pointing to temp dir.

    Returns:
        SessionService instance.
    """
    return SessionService(settings=test_settings)


@pytest.fixture
def cron_service(test_settings: Settings) -> CronService:
    """Return a CronService using the mock home.

    Args:
        test_settings: Test settings pointing to temp dir.

    Returns:
        CronService instance.
    """
    return CronService(settings=test_settings)


# ---------------------------------------------------------------------------
# HTTP client fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def async_client(
    test_settings: Settings,
    file_service: FileService,
    agent_service: AgentService,
    config_service: ConfigService,
    gateway_service: GatewayService,
    cron_service: CronService,
    session_service: SessionService,
) -> AsyncGenerator[AsyncClient, None]:
    """Return an async HTTP client wired to the test FastAPI app.

    Overrides ALL dependency injections so no real ~/.openclaw/ is touched.

    Args:
        test_settings: Settings pointing to temp dir.
        file_service: FileService pointing to temp dir.
        agent_service: AgentService pointing to temp dir.
        config_service: ConfigService pointing to temp dir.
        gateway_service: GatewayService pointing to temp dir.
        cron_service: CronService pointing to temp dir.
        session_service: SessionService pointing to temp dir.

    Yields:
        AsyncClient that sends requests to the test app.
    """
    from app.dependencies import (
        get_agent_service,
        get_config_service,
        get_cron_service,
        get_file_service,
        get_gateway_service,
        get_session_service,
        get_settings,
    )

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_file_service] = lambda: file_service
    app.dependency_overrides[get_agent_service] = lambda: agent_service
    app.dependency_overrides[get_config_service] = lambda: config_service
    app.dependency_overrides[get_gateway_service] = lambda: gateway_service
    app.dependency_overrides[get_cron_service] = lambda: cron_service
    app.dependency_overrides[get_session_service] = lambda: session_service

    # Disable rate limiter in tests (env set below ensures limiter.enabled=False)
    import os
    os.environ["TESTING"] = "1"

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://localhost",  # Must match allowed hosts
        headers={"Host": "localhost"},  # Pass host validation middleware
    ) as client:
        yield client

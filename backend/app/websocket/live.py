"""WebSocket live-update handler — WS /ws/live

Message protocol (R11):
  Every message is a JSON object with this envelope:

    {
      "type":      "gateway_status" | "file_changed" | "error" | "ping",
      "timestamp": "<ISO-8601 UTC>",
      "payload":   { ... }
    }

Client rules:
  - On "ping" → respond with {"type": "pong"}
  - On disconnect → reconnect with exponential backoff (handled in frontend)

Server sends:
  - "ping"           every 30 seconds (keepalive)
  - "gateway_status" every 10 seconds
  - "file_changed"   when a watched workspace file changes (debounced 500 ms)

File watching scope (R1.2 — specific files only, NOT recursive):
  Per-agent:   AGENTS.md, SOUL.md, IDENTITY.md, USER.md, TOOLS.md,
               MEMORY.md, ACTIVE.md, HEARTBEAT.md
  Global:      ~/.openclaw/openclaw.json
               ~/.openclaw/sessions/sessions.json
"""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
from fastapi import WebSocket, WebSocketDisconnect
from watchfiles import Change, awatch

from app.config import settings as _settings
from app.services.agent_service import WORKSPACE_FILES, AgentService
from app.services.gateway_service import GatewayService

logger = structlog.get_logger(__name__)

# Intervals
_PING_INTERVAL_S = 30
_STATUS_INTERVAL_S = 10
_DEBOUNCE_S = 0.5


# ---------------------------------------------------------------------------
# Connection manager (single connection — localhost personal tool)
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Manage a single active WebSocket connection."""

    def __init__(self) -> None:
        self._ws: WebSocket | None = None

    async def connect(self, ws: WebSocket) -> None:
        """Accept and store a new WebSocket connection."""
        await ws.accept()
        self._ws = ws
        logger.info("websocket_connected")

    def disconnect(self) -> None:
        """Mark the connection as closed."""
        self._ws = None
        logger.info("websocket_disconnected")

    async def send(self, data: dict) -> None:
        """Send a JSON message to the connected client.

        Args:
            data: Dict to serialise and send.
        """
        if self._ws is not None:
            try:
                await self._ws.send_text(json.dumps(data))
            except Exception:  # noqa: BLE001
                self.disconnect()

    @property
    def connected(self) -> bool:
        """True if a client is currently connected."""
        return self._ws is not None


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Public WebSocket handler
# ---------------------------------------------------------------------------

async def websocket_handler(
    websocket: WebSocket,
    agent_svc: AgentService,
    gateway_svc: GatewayService,
) -> None:
    """Handle a single WebSocket connection for live updates.

    Spawns three background tasks:
      1. Ping loop (every 30 s)
      2. Gateway status loop (every 10 s)
      3. File watcher loop

    Args:
        websocket: The accepted WebSocket connection.
        agent_svc: AgentService for workspace path resolution.
        gateway_svc: GatewayService for status polling.
    """
    await manager.connect(websocket)
    tasks: list[asyncio.Task] = []

    try:
        # Start background tasks
        tasks = [
            asyncio.create_task(
                _ping_loop(manager), name="ws-ping"
            ),
            asyncio.create_task(
                _gateway_status_loop(manager, gateway_svc), name="ws-gateway-status"
            ),
            asyncio.create_task(
                _file_watcher_loop(manager, agent_svc), name="ws-file-watcher"
            ),
        ]

        # Receive loop — handle pong and disconnect
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception:  # noqa: BLE001
                break

            try:
                msg = json.loads(raw)
                if msg.get("type") == "pong":
                    pass  # Heartbeat acknowledged — nothing to do
            except json.JSONDecodeError:
                pass

    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        manager.disconnect()


# ---------------------------------------------------------------------------
# Background task helpers
# ---------------------------------------------------------------------------

async def _ping_loop(mgr: ConnectionManager) -> None:
    """Send a ping message every _PING_INTERVAL_S seconds.

    Args:
        mgr: Active ConnectionManager.
    """
    while True:
        await asyncio.sleep(_PING_INTERVAL_S)
        if not mgr.connected:
            break
        await mgr.send(_envelope("ping", {}))


async def _gateway_status_loop(
    mgr: ConnectionManager, gateway_svc: GatewayService
) -> None:
    """Send gateway_status every _STATUS_INTERVAL_S seconds.

    Args:
        mgr: Active ConnectionManager.
        gateway_svc: GatewayService to query.
    """
    while True:
        await asyncio.sleep(_STATUS_INTERVAL_S)
        if not mgr.connected:
            break
        try:
            status = await gateway_svc.get_status()
            await mgr.send(
                _envelope(
                    "gateway_status",
                    {
                        "running": status.running,
                        "pid": status.pid,
                        "uptime": status.uptime,
                        "error": status.error,
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001
            await mgr.send(
                _envelope("error", {"message": f"Gateway status error: {exc}"})
            )


async def _file_watcher_loop(
    mgr: ConnectionManager, agent_svc: AgentService
) -> None:
    """Watch specific workspace files and emit file_changed events.

    Watches only the files listed in WORKSPACE_FILES for each discovered
    agent, plus the global config and sessions files.  Debounces events
    by _DEBOUNCE_S seconds to avoid flooding on bulk writes.

    Args:
        mgr: Active ConnectionManager.
        agent_svc: AgentService to discover agent workspaces.
    """
    watch_paths = await _build_watch_paths(agent_svc)
    if not watch_paths:
        logger.warning("file_watcher_no_paths")
        return

    logger.info("file_watcher_started", paths=[str(p) for p in watch_paths])

    # watchfiles watches the parent directories and we filter by filename
    # Watch the set of directories that contain our target files
    watch_dirs = {p.parent for p in watch_paths if p.parent.exists()}
    target_names = {p.name for p in watch_paths} | set(WORKSPACE_FILES)

    try:
        async for changes in awatch(*watch_dirs, debounce=int(_DEBOUNCE_S * 1000)):
            if not mgr.connected:
                break
            for change_type, path_str in changes:
                path = Path(path_str)
                if path.name not in target_names:
                    continue
                # Find which agent this file belongs to
                agent_id = _agent_id_for_path(path, agent_svc)
                await mgr.send(
                    _envelope(
                        "file_changed",
                        {
                            "agent_id": agent_id,
                            "path": str(path),
                            "name": path.name,
                            "change": _change_name(change_type),
                        },
                    )
                )
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("file_watcher_error", error=str(exc))
        if mgr.connected:
            await mgr.send(_envelope("error", {"message": f"File watcher error: {exc}"}))


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

async def _build_watch_paths(agent_svc: AgentService) -> list[Path]:
    """Build the list of specific files to watch.

    Args:
        agent_svc: AgentService for workspace discovery.

    Returns:
        List of absolute Paths to watch.
    """
    paths: list[Path] = []

    # Global files
    global_files = [
        _settings.config_path,
        _settings.sessions_path,
    ]
    for p in global_files:
        if p.parent.exists():
            paths.append(p)

    # Per-agent files
    try:
        agent_list = await agent_svc.list_agents()
        for agent in agent_list.agents:
            workspace = agent_svc.resolve_agent_workspace(agent.id)
            if workspace.exists():
                for fname in WORKSPACE_FILES:
                    candidate = workspace / fname
                    paths.append(candidate)
    except Exception as exc:  # noqa: BLE001
        logger.warning("watch_paths_agent_discovery_error", error=str(exc))

    return paths


def _agent_id_for_path(path: Path, agent_svc: AgentService) -> str | None:
    """Determine which agent a changed file path belongs to.

    Args:
        path: Changed file path.
        agent_svc: AgentService.

    Returns:
        Agent ID string or None if it is a global file.
    """
    home = _settings.OPENCLAW_HOME
    # Check if it's the main workspace
    main_ws = home / "workspace"
    if str(path).startswith(str(main_ws)):
        return "main"
    # Check workspace-{id} patterns
    parent_name = path.parent.name
    if parent_name.startswith("workspace-"):
        return parent_name[len("workspace-"):]
    return None


def _change_name(change: Change) -> str:
    """Convert watchfiles Change enum to a string.

    Args:
        change: watchfiles Change type.

    Returns:
        String label.
    """
    try:
        return change.name.lower()  # "added", "modified", "deleted"
    except AttributeError:
        return "modified"


def _envelope(event_type: str, payload: dict[str, Any]) -> dict:
    """Build a standard WebSocket message envelope.

    Args:
        event_type: One of gateway_status, file_changed, error, ping.
        payload: Event-specific payload dict.

    Returns:
        Dict matching the defined WebSocket message protocol.
    """
    return {
        "type": event_type,
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": payload,
    }

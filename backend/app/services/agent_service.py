"""Agent discovery service.

Discovers all configured OpenClaw agents, resolves their workspaces,
and reads metadata for each.

Resolution strategy for workspace paths:
  - "main"            → ~/.openclaw/workspace/
  - anything else     → ~/.openclaw/workspace-{id}/ (if it exists)
                        else ~/.openclaw/agents/{id}/  (fallback)

This logic lives in ONE place: resolve_agent_workspace().
No other code may construct agent paths — it must call this function.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import structlog

from app.config import Settings
from app.models.agent import AgentDetailResponse, AgentFileInfo, AgentListResponse, AgentSummary
from app.services.file_service import FileService

logger = structlog.get_logger(__name__)

# Files worth listing in an agent's workspace
WORKSPACE_FILES = {
    "AGENTS.md",
    "SOUL.md",
    "IDENTITY.md",
    "USER.md",
    "TOOLS.md",
    "MEMORY.md",
    "ACTIVE.md",
    "HEARTBEAT.md",
    "PROJECT.md",
}

_STATUS_ACTIVE_THRESHOLD_SECONDS = 600  # 10 minutes


class AgentService:
    """Discover and describe OpenClaw agents.

    Args:
        settings: Application settings.
        file_service: FileService used to read workspace files safely.
    """

    def __init__(self, settings: Settings, file_service: FileService) -> None:
        """Initialise the agent service.

        Args:
            settings: Application settings.
            file_service: Sandboxed file service.
        """
        self._settings = settings
        self._fs = file_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve_agent_workspace(self, agent_id: str) -> Path:
        """Return the workspace directory for an agent.

        This is THE ONLY function that encapsulates the main-agent
        special case.  Do NOT construct agent paths anywhere else.

        Args:
            agent_id: Agent identifier string.

        Returns:
            Absolute Path to the agent's workspace directory.
        """
        if agent_id == "main":
            return self._settings.OPENCLAW_HOME / "workspace"

        # Prefer workspace-{id} sibling directory
        ws = self._settings.OPENCLAW_HOME / f"workspace-{agent_id}"
        if ws.exists():
            return ws

        # Fall back to agents/{id}
        agents_path = self._settings.OPENCLAW_HOME / "agents" / agent_id
        if agents_path.exists():
            return agents_path

        # Neither exists — return workspace-{id} as canonical default
        return ws

    async def list_agents(self) -> AgentListResponse:
        """List all discovered agents.

        Discovery merges:
        1. Hardcoded "main" agent.
        2. Directories in ~/.openclaw/agents/.
        3. Agents listed in openclaw.json → agents section.

        Returns:
            AgentListResponse with summary info for each agent.
        """
        agent_ids = await self._discover_agent_ids()
        openclaw_cfg = await self._load_openclaw_config()
        sessions_index = await self._load_sessions_index()

        summaries: list[AgentSummary] = []
        for aid in agent_ids:
            try:
                summary = await self._build_summary(aid, openclaw_cfg, sessions_index)
                summaries.append(summary)
            except Exception as exc:  # noqa: BLE001
                logger.warning("agent_summary_error", agent_id=aid, error=str(exc))
                summaries.append(
                    AgentSummary(
                        id=aid,
                        name=aid.title(),
                        model="unknown",
                        status="unknown",
                        last_activity=None,
                    )
                )

        return AgentListResponse(agents=summaries, total=len(summaries))

    async def get_agent(self, agent_id: str) -> AgentDetailResponse:
        """Return full detail for a single agent.

        Args:
            agent_id: Agent identifier string.

        Returns:
            AgentDetailResponse with workspace files and metadata.

        Raises:
            FileNotFoundError: If the agent is not found / workspace missing.
        """
        openclaw_cfg = await self._load_openclaw_config()
        sessions_index = await self._load_sessions_index()
        workspace = self.resolve_agent_workspace(agent_id)

        if not workspace.exists():
            raise FileNotFoundError(
                f"Agent workspace not found for '{agent_id}': {workspace}"
            )

        files = await self._list_workspace_files(workspace)
        name, model = self._extract_agent_meta(agent_id, openclaw_cfg, sessions_index)
        last_activity = self._last_activity(agent_id, sessions_index)
        status = self._compute_status(last_activity, workspace)

        return AgentDetailResponse(
            id=agent_id,
            name=name,
            model=model,
            workspace=str(workspace),
            files=files,
            last_activity=last_activity,
            status=status,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _discover_agent_ids(self) -> list[str]:
        """Discover all agent IDs from filesystem and config.

        Returns:
            Deduplicated list of agent ID strings, "main" always first.
        """
        ids: list[str] = ["main"]

        # Scan ~/.openclaw/agents/ directory
        agents_dir = self._settings.agents_dir
        if agents_dir.exists():
            for entry in sorted(agents_dir.iterdir()):
                if entry.is_dir() and entry.name not in ids:
                    ids.append(entry.name)

        # Scan workspace-* directories inside OPENCLAW_HOME
        home = self._settings.OPENCLAW_HOME
        if home.exists():
            for entry in sorted(home.iterdir()):
                if (
                    entry.is_dir()
                    and entry.name.startswith("workspace-")
                ):
                    aid = entry.name[len("workspace-"):]
                    if aid not in ids:
                        ids.append(aid)

        # Also include agents listed in openclaw.json
        cfg = await self._load_openclaw_config()
        agents_in_cfg = cfg.get("agents", {})
        if isinstance(agents_in_cfg, dict):
            for key, val in agents_in_cfg.items():
                # Skip meta-keys and entries whose value is not a dict
                if key not in ids and key != "defaults" and isinstance(val, dict):
                    ids.append(key)

        return ids

    async def _load_openclaw_config(self) -> dict:
        """Load and parse openclaw.json, returning empty dict on failure.

        Returns:
            Parsed config dict (may be empty if file is missing/malformed).
        """
        config_path = self._settings.config_path
        if not config_path.exists():
            return {}
        try:
            content, _ = await self._fs.read_file(config_path)
            return json.loads(content)
        except Exception as exc:  # noqa: BLE001
            logger.warning("openclaw_config_load_error", error=str(exc))
            return {}

    async def _load_sessions_index(self) -> dict:
        """Load sessions.json for last-activity timestamps.

        Returns:
            Sessions dict (may be empty if file is missing).
        """
        sessions_path = self._settings.sessions_path
        if not sessions_path.exists():
            return {}
        try:
            content, _ = await self._fs.read_file(sessions_path)
            return json.loads(content)
        except Exception as exc:  # noqa: BLE001
            logger.debug("sessions_load_error", error=str(exc))
            return {}

    async def _list_workspace_files(self, workspace: Path) -> list[AgentFileInfo]:
        """List known files in an agent workspace.

        Scans the workspace for files in WORKSPACE_FILES plus the memory/
        sub-directory.

        Args:
            workspace: Absolute path to the workspace directory.

        Returns:
            List of AgentFileInfo objects sorted by name.
        """
        files: list[AgentFileInfo] = []
        if not workspace.exists():
            return files

        # Top-level known files — filter against WORKSPACE_FILES set
        for fname in sorted(workspace.iterdir(), key=lambda p: p.name):
            if fname.is_file() and fname.name in WORKSPACE_FILES:
                try:
                    stat = fname.stat()
                    files.append(
                        AgentFileInfo(
                            name=fname.name,
                            size=stat.st_size,
                            mtime=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                        )
                    )
                except OSError:
                    pass

        return files

    def _extract_agent_meta(
        self, agent_id: str, cfg: dict, sessions: dict | None = None
    ) -> tuple[str, str]:
        """Extract display name and model from sessions + openclaw.json.

        Model priority:
        1. Most recent session model (from sessions.json)
        2. Agent-specific config in openclaw.json
        3. Default config in openclaw.json
        4. "unknown"

        Args:
            agent_id: Agent identifier string.
            cfg: Parsed openclaw.json dict.
            sessions: Parsed sessions.json dict (optional).

        Returns:
            Tuple of (display_name, model_string).
        """
        # Try session model first (most accurate for what agent actually used)
        session_model = self._session_model(agent_id, sessions) if sessions else None

        agents_cfg = cfg.get("agents", {})
        defaults = agents_cfg.get("defaults", {}) if isinstance(agents_cfg, dict) else {}
        raw_cfg = agents_cfg.get(agent_id, {}) if isinstance(agents_cfg, dict) else {}
        # Guard: agent cfg must be a dict (could be a list in unusual configs)
        agent_cfg = raw_cfg if isinstance(raw_cfg, dict) else {}

        model_raw = (
            agent_cfg.get("model")
            or defaults.get("model")
            or "unknown"
        )
        # model may be a dict like {"primary": "...", "fallback": [...]}
        if isinstance(model_raw, dict):
            config_model = (
                model_raw.get("primary")
                or next(
                    (v for v in model_raw.values() if isinstance(v, str)),
                    "unknown",
                )
            )
        elif isinstance(model_raw, str):
            config_model = model_raw
        else:
            config_model = "unknown"

        model = session_model or config_model

        # Try to read name from workspace IDENTITY.md or SOUL.md
        name = agent_cfg.get("name") or agent_id.title()

        return name, model

    def _session_model(self, agent_id: str, sessions: dict) -> str | None:
        """Find the model from the most recent session for this agent.

        Args:
            agent_id: Agent identifier string.
            sessions: Parsed sessions.json dict.

        Returns:
            Model string from the most recent session, or None.
        """
        if not isinstance(sessions, dict):
            return None

        prefix = f"agent:{agent_id}:"
        latest_ts: int | float = -1
        latest_model: str | None = None

        for key, session_data in sessions.items():
            if not key.startswith(prefix):
                continue
            if not isinstance(session_data, dict):
                continue
            updated_at = session_data.get("updatedAt")
            if not isinstance(updated_at, (int, float)):
                continue
            if updated_at > latest_ts:
                model = session_data.get("model")
                if isinstance(model, str) and model:
                    latest_ts = updated_at
                    latest_model = model

        return latest_model

    def _last_activity(self, agent_id: str, sessions: dict) -> datetime | None:
        """Find most recent updatedAt across all sessions for this agent.

        sessions.json keys are session keys like "agent:main:main",
        "agent:main:subagent:uuid", "agent:main:whatsapp:...".
        Values are dicts with updatedAt as int (ms Unix timestamp).

        Args:
            agent_id: Agent identifier string.
            sessions: Parsed sessions.json dict.

        Returns:
            UTC datetime of last activity, or None if unknown.
        """
        if not isinstance(sessions, dict):
            return None

        prefix = f"agent:{agent_id}:"
        latest: datetime | None = None

        for key, session_data in sessions.items():
            if not key.startswith(prefix):
                continue
            if not isinstance(session_data, dict):
                continue
            updated_at = session_data.get("updatedAt")
            if not isinstance(updated_at, (int, float)):
                continue
            try:
                ts = datetime.fromtimestamp(updated_at / 1000, tz=timezone.utc)
                if latest is None or ts > latest:
                    latest = ts
            except (ValueError, OSError, OverflowError):
                pass

        return latest

    def _compute_status(
        self, last_activity: datetime | None, workspace: Path
    ) -> str:
        """Compute a human-friendly status string for an agent.

        Args:
            last_activity: UTC datetime of last activity (may be None).
            workspace: Workspace path (used for existence check).

        Returns:
            One of: "active", "idle", "stopped", "unknown".
        """
        if not workspace.exists():
            return "stopped"
        if last_activity is None:
            return "idle"
        now = datetime.now(timezone.utc)
        delta = (now - last_activity).total_seconds()
        if delta <= _STATUS_ACTIVE_THRESHOLD_SECONDS:
            return "active"
        return "idle"

    async def _build_summary(
        self,
        agent_id: str,
        openclaw_cfg: dict,
        sessions_index: dict,
    ) -> AgentSummary:
        """Build a summary for a single agent.

        Args:
            agent_id: Agent identifier string.
            openclaw_cfg: Parsed openclaw.json.
            sessions_index: Parsed sessions.json.

        Returns:
            AgentSummary instance.
        """
        workspace = self.resolve_agent_workspace(agent_id)
        name, model = self._extract_agent_meta(agent_id, openclaw_cfg, sessions_index)
        last_activity = self._last_activity(agent_id, sessions_index)
        status = self._compute_status(last_activity, workspace)

        return AgentSummary(
            id=agent_id,
            name=name,
            model=model,
            status=status,
            last_activity=last_activity,
        )

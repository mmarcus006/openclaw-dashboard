"""Gateway CLI wrapper service.

Security rules (R6):
  - ALWAYS use asyncio.create_subprocess_exec() with explicit argument lists.
  - NEVER use create_subprocess_shell() or string interpolation.
  - ALWAYS validate the action against GatewayAction enum BEFORE calling subprocess.
  - ALL subprocess calls have a 10-second timeout.
  - Parse CLI output defensively — if parsing fails, return degraded response.
"""

import asyncio
import shutil
from collections import deque

import structlog

from app.config import Settings
from app.models.gateway import (
    CommandResponse,
    GatewayAction,
    GatewayCommandEntry,
    GatewayHistoryResponse,
    GatewayStatusResponse,
)
from app.utils import now_iso

logger = structlog.get_logger(__name__)

_SUBPROCESS_TIMEOUT = 10  # seconds


class GatewayService:
    """Thin wrapper around the openclaw CLI for gateway operations.

    Args:
        settings: Application settings (used to find HOME and CLI path).
    """

    _MAX_HISTORY = 10

    def __init__(self, settings: Settings) -> None:
        """Initialise GatewayService.

        Args:
            settings: Application settings.
        """
        self._settings = settings
        self._history: deque[GatewayCommandEntry] = deque(maxlen=self._MAX_HISTORY)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_status(self) -> GatewayStatusResponse:
        """Run ``openclaw gateway status`` and parse the result.

        Returns a degraded response (running=False, error=<msg>) rather than
        raising an exception if the CLI is unavailable or output is unparseable.

        Returns:
            GatewayStatusResponse with current gateway state.
        """
        cli = shutil.which("openclaw")
        if cli is None:
            return GatewayStatusResponse(
                running=False,
                pid=None,
                uptime=None,
                channels={},
                error="openclaw CLI not found in PATH",
            )

        try:
            stdout, stderr, returncode = await self._run_cli("gateway", "status")
        except TimeoutError:
            return GatewayStatusResponse(
                running=False,
                error="Timed out querying gateway status",
            )
        except Exception as exc:  # noqa: BLE001
            return GatewayStatusResponse(
                running=False,
                error=f"CLI error: {exc}",
            )

        return self._parse_status(stdout, stderr, returncode)

    async def run_command(self, action: GatewayAction) -> CommandResponse:
        """Execute a gateway command (start / stop / restart).

        The action is validated at the type-system level via GatewayAction enum
        before this method is called, so no further validation is needed here.

        Args:
            action: One of GatewayAction.START, STOP, or RESTART.

        Returns:
            CommandResponse indicating success/failure.

        Raises:
            TimeoutError: If the subprocess does not complete within 10 seconds.
            FileNotFoundError: If the openclaw CLI is not found.
        """
        cli = shutil.which("openclaw")
        if cli is None:
            raise FileNotFoundError("openclaw CLI not found in PATH")

        logger.info("gateway_command", action=action.value)

        try:
            stdout, stderr, returncode = await self._run_cli("gateway", action.value)
        except TimeoutError as exc:
            raise TimeoutError(
                f"Gateway command '{action.value}' timed out after {_SUBPROCESS_TIMEOUT}s"
            ) from exc

        output = (stdout + "\n" + stderr).strip() if (stdout or stderr) else None
        success = returncode == 0

        self._history.appendleft(GatewayCommandEntry(
            command=action.value,
            timestamp=now_iso(),
            exit_code=returncode,
            output=output[:500] if output else None,
        ))

        return CommandResponse(
            success=success,
            action=action,
            message=(
                f"Gateway {action.value} {'succeeded' if success else 'failed'}."
            ),
            output=output or None,
        )

    def get_history(self) -> GatewayHistoryResponse:
        """Return recent command history (in-memory, resets on restart)."""
        commands = list(self._history)
        return GatewayHistoryResponse(commands=commands, total=len(commands))

    def is_installed(self) -> bool:
        """Return True if the openclaw CLI is available in PATH.

        Returns:
            True if the CLI exists, False otherwise.
        """
        return shutil.which("openclaw") is not None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run_cli(self, *args: str) -> tuple[str, str, int]:
        """Run ``openclaw <args>`` and return (stdout, stderr, returncode).

        Uses create_subprocess_exec — NEVER create_subprocess_shell.

        Args:
            *args: Positional arguments to pass to the openclaw CLI.

        Returns:
            Tuple of (stdout text, stderr text, return code).

        Raises:
            TimeoutError: If the process does not finish within _SUBPROCESS_TIMEOUT.
        """
        proc = await asyncio.create_subprocess_exec(
            "openclaw",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            raw_out, raw_err = await asyncio.wait_for(
                proc.communicate(), timeout=_SUBPROCESS_TIMEOUT
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()  # drain pipes after kill
            raise TimeoutError(
                f"openclaw {' '.join(args)} timed out after {_SUBPROCESS_TIMEOUT}s"
            )

        stdout = raw_out.decode("utf-8", errors="replace").strip() if raw_out else ""
        stderr = raw_err.decode("utf-8", errors="replace").strip() if raw_err else ""
        returncode = proc.returncode if proc.returncode is not None else -1

        return stdout, stderr, returncode

    def _parse_status(
        self, stdout: str, stderr: str, returncode: int
    ) -> GatewayStatusResponse:
        """Parse ``openclaw gateway status`` output into a structured response.

        Parsing is defensive — any failure returns a degraded response.

        Args:
            stdout: Standard output from the CLI.
            stderr: Standard error from the CLI.
            returncode: Process exit code.

        Returns:
            GatewayStatusResponse (may be degraded if parsing fails).
        """
        _ = stdout + "\n" + stderr  # kept for future debug logging

        # Non-zero exit typically means the gateway is not running
        if returncode != 0:
            return GatewayStatusResponse(
                running=False,
                error=stderr or f"Exit code {returncode}",
            )

        try:
            running = _detect_running(stdout)
            pid = _extract_pid(stdout)
            uptime = _extract_uptime(stdout)
            channels = _extract_channels(stdout)

            return GatewayStatusResponse(
                running=running,
                pid=pid,
                uptime=uptime,
                channels=channels,
                error=None,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("gateway_status_parse_failed", error=str(exc), stdout=stdout[:500])
            return GatewayStatusResponse(
                running=False,
                error=f"Could not parse CLI output: {exc}",
            )


# ---------------------------------------------------------------------------
# Parsing helpers — all defensive, never raise
# ---------------------------------------------------------------------------

def _detect_running(text: str) -> bool:
    """Detect whether the gateway reports itself as running.

    Args:
        text: CLI stdout text.

    Returns:
        True if running indicators found.
    """
    text_lower = text.lower()
    if "running" in text_lower and "not running" not in text_lower:
        return True
    if "started" in text_lower or "online" in text_lower:
        return True
    return False


def _extract_pid(text: str) -> int | None:
    """Extract PID from gateway status output.

    Args:
        text: CLI stdout text.

    Returns:
        Integer PID, or None if not found.
    """
    import re
    m = re.search(r"pid[:\s]+(\d+)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def _extract_uptime(text: str) -> str | None:
    """Extract uptime string from gateway status output.

    Args:
        text: CLI stdout text.

    Returns:
        Uptime string (e.g. "2h 15m"), or None if not found.
    """
    import re
    m = re.search(r"uptime[:\s]+([^\n]+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def _extract_channels(text: str) -> dict:
    """Extract active channel map from gateway status output.

    Args:
        text: CLI stdout text.

    Returns:
        Dict of channel name → status (may be empty).
    """
    # Placeholder — format depends on openclaw CLI output
    return {}

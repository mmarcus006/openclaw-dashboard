"""Tests for /api/gateway/* endpoints.

Covers:
  - GET /api/gateway/status returns structured response
  - POST /api/gateway/start, stop, restart call correct subprocess
  - Invalid action returns 422 (enum validation)
  - Subprocess timeout returns 504
  - Degraded response when CLI is unavailable
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


class TestGatewayStatus:
    """Tests for GET /api/gateway/status."""

    async def test_gateway_status_returns_200(self, async_client: AsyncClient):
        """GET /api/gateway/status always returns 200 (even degraded)."""
        with patch("shutil.which", return_value=None):
            response = await async_client.get("/api/gateway/status")
        assert response.status_code == 200

    async def test_gateway_status_has_running_field(self, async_client: AsyncClient):
        """Response always includes a 'running' boolean field."""
        with patch("shutil.which", return_value=None):
            response = await async_client.get("/api/gateway/status")
        data = response.json()
        assert "running" in data
        assert isinstance(data["running"], bool)

    async def test_gateway_status_degraded_when_cli_missing(
        self, async_client: AsyncClient
    ):
        """When openclaw CLI is not found, response has running=False and error message."""
        with patch("shutil.which", return_value=None):
            response = await async_client.get("/api/gateway/status")
        data = response.json()
        assert data["running"] is False
        assert data["error"] is not None
        assert "openclaw" in data["error"].lower() or "not found" in data["error"].lower()

    async def test_gateway_status_structure_has_all_fields(
        self, async_client: AsyncClient
    ):
        """Response includes running, pid, uptime, channels, error fields."""
        with patch("shutil.which", return_value=None):
            response = await async_client.get("/api/gateway/status")
        data = response.json()
        assert "running" in data
        # pid, uptime, channels, error are all optional/nullable
        for field in ("pid", "uptime", "channels", "error"):
            assert field in data

    async def test_gateway_status_parsed_when_running(
        self, async_client: AsyncClient
    ):
        """When CLI is found and returns 'Running', running=True."""
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "app.services.gateway_service.GatewayService._run_cli",
                new_callable=AsyncMock,
                return_value=("Gateway is Running\npid: 12345\nuptime: 1h 30m", "", 0),
            ),
        ):
            response = await async_client.get("/api/gateway/status")
        data = response.json()
        assert data["running"] is True
        assert data["pid"] == 12345

    async def test_gateway_status_not_running_on_nonzero_exit(
        self, async_client: AsyncClient
    ):
        """Non-zero exit code results in running=False."""
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "app.services.gateway_service.GatewayService._run_cli",
                new_callable=AsyncMock,
                return_value=("", "Gateway is not running", 1),
            ),
        ):
            response = await async_client.get("/api/gateway/status")
        data = response.json()
        assert data["running"] is False


class TestGatewayCommands:
    """Tests for POST /api/gateway/{action}."""

    async def test_gateway_start_returns_200(self, async_client: AsyncClient):
        """POST /api/gateway/start returns 200."""
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

    async def test_gateway_stop_returns_200(self, async_client: AsyncClient):
        """POST /api/gateway/stop returns 200."""
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "app.services.gateway_service.GatewayService._run_cli",
                new_callable=AsyncMock,
                return_value=("Gateway stopped.", "", 0),
            ),
        ):
            response = await async_client.post("/api/gateway/stop")
        assert response.status_code == 200

    async def test_gateway_restart_returns_200(self, async_client: AsyncClient):
        """POST /api/gateway/restart returns 200."""
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "app.services.gateway_service.GatewayService._run_cli",
                new_callable=AsyncMock,
                return_value=("Gateway restarted.", "", 0),
            ),
        ):
            response = await async_client.post("/api/gateway/restart")
        assert response.status_code == 200

    async def test_gateway_start_uses_exec_not_shell(self, async_client: AsyncClient):
        """Gateway start calls _run_cli with 'gateway', 'start' args (exec, not shell)."""
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "app.services.gateway_service.GatewayService._run_cli",
                new_callable=AsyncMock,
                return_value=("OK", "", 0),
            ) as mock_run,
        ):
            await async_client.post("/api/gateway/start")
        # The service should have been called with ("gateway", "start")
        mock_run.assert_called_once_with("gateway", "start")

    async def test_gateway_stop_uses_exec_not_shell(self, async_client: AsyncClient):
        """Gateway stop calls _run_cli with 'gateway', 'stop' args."""
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "app.services.gateway_service.GatewayService._run_cli",
                new_callable=AsyncMock,
                return_value=("OK", "", 0),
            ) as mock_run,
        ):
            await async_client.post("/api/gateway/stop")
        mock_run.assert_called_once_with("gateway", "stop")

    async def test_gateway_restart_uses_exec_not_shell(self, async_client: AsyncClient):
        """Gateway restart calls _run_cli with 'gateway', 'restart' args."""
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "app.services.gateway_service.GatewayService._run_cli",
                new_callable=AsyncMock,
                return_value=("OK", "", 0),
            ) as mock_run,
        ):
            await async_client.post("/api/gateway/restart")
        mock_run.assert_called_once_with("gateway", "restart")

    async def test_gateway_command_response_has_success_field(
        self, async_client: AsyncClient
    ):
        """Command response includes a 'success' boolean."""
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "app.services.gateway_service.GatewayService._run_cli",
                new_callable=AsyncMock,
                return_value=("OK", "", 0),
            ),
        ):
            response = await async_client.post("/api/gateway/start")
        data = response.json()
        assert "success" in data
        assert isinstance(data["success"], bool)

    async def test_gateway_command_response_has_action_field(
        self, async_client: AsyncClient
    ):
        """Command response includes the 'action' field matching what was requested."""
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "app.services.gateway_service.GatewayService._run_cli",
                new_callable=AsyncMock,
                return_value=("OK", "", 0),
            ),
        ):
            response = await async_client.post("/api/gateway/restart")
        data = response.json()
        assert "action" in data
        assert data["action"] == "restart"

    async def test_gateway_invalid_action_returns_422(self, async_client: AsyncClient):
        """POST /api/gateway/delete (invalid action) returns 422."""
        response = await async_client.post("/api/gateway/delete")
        assert response.status_code == 422

    async def test_gateway_invalid_action_shell_injection_not_200(
        self, async_client: AsyncClient
    ):
        """POST with shell injection string in action is never accepted as a valid command.

        httpx URL-encodes the path, so FastAPI may 307-redirect or 422-reject.
        The critical property is: it must NOT be 200 (i.e., it must not succeed).
        The enum validation ensures the value never reaches the subprocess.
        """
        response = await async_client.post(
            "/api/gateway/start%3Brm+-rf+%2F",  # pre-encoded: "start;rm -rf /"
            follow_redirects=False,
        )
        # Any rejection (307 redirect, 404, 422) means the attack is blocked
        assert response.status_code != 200

    async def test_gateway_cli_missing_returns_404(self, async_client: AsyncClient):
        """POST /api/gateway/start returns 404 when CLI not found."""
        with patch("shutil.which", return_value=None):
            response = await async_client.post("/api/gateway/start")
        assert response.status_code == 404

    async def test_gateway_timeout_returns_504(self, async_client: AsyncClient):
        """POST /api/gateway/start returns 504 when subprocess times out."""
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "app.services.gateway_service.GatewayService._run_cli",
                side_effect=TimeoutError("timed out"),
            ),
        ):
            response = await async_client.post("/api/gateway/start")
        assert response.status_code == 504

    async def test_gateway_timeout_has_error_envelope(self, async_client: AsyncClient):
        """504 response uses the standard error envelope."""
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "app.services.gateway_service.GatewayService._run_cli",
                side_effect=TimeoutError("timed out"),
            ),
        ):
            response = await async_client.post("/api/gateway/start")
        data = response.json()
        assert "error" in data


class TestGatewaySubprocessExec:
    """Tests confirming create_subprocess_exec is used (not create_subprocess_shell)."""

    def test_no_create_subprocess_shell_in_gateway_service(self):
        """Grep code lines: create_subprocess_shell must not be called in gateway_service.py.

        Note: The string may appear in comments/docstrings saying "NEVER use X",
        which is fine. We only check actual code lines (not starting with # or quotes).
        """
        service_file = (
            __file__.replace("tests/test_gateway.py", "")
            + "app/services/gateway_service.py"
        )
        from pathlib import Path as P
        code_lines = _extract_code_lines(P(service_file).read_text())
        assert "create_subprocess_shell" not in code_lines, (
            "gateway_service.py must NEVER call create_subprocess_shell (R6)"
        )

    def test_create_subprocess_exec_used_in_gateway_service(self):
        """Grep: create_subprocess_exec IS used in gateway_service.py."""
        service_file = (
            __file__.replace("tests/test_gateway.py", "")
            + "app/services/gateway_service.py"
        )
        from pathlib import Path as P
        source = P(service_file).read_text()
        assert "create_subprocess_exec" in source

    def test_no_create_subprocess_shell_in_any_source(self):
        """Grep code lines: create_subprocess_shell must not be called in any app source file.

        Comment lines are excluded — docstrings warning against usage are fine.
        """
        from pathlib import Path as P
        app_dir = P(__file__).parent.parent / "app"
        violations = []
        for py_file in app_dir.rglob("*.py"):
            code_lines = _extract_code_lines(py_file.read_text())
            if "create_subprocess_shell" in code_lines:
                violations.append(str(py_file))
        assert violations == [], (
            f"create_subprocess_shell called in: {violations} — NEVER use shell subprocess (R6)"
        )


def _extract_code_lines(source: str) -> str:
    """Return only non-comment, non-docstring lines from Python source.

    Used by grep-style tests to avoid false positives from safety warnings
    in comments/docstrings.

    Args:
        source: Full Python source code as a string.

    Returns:
        Concatenated string of code lines only.
    """
    import tokenize
    import io

    code_lines = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
        # Collect line numbers that are purely string/comment tokens (docstrings, comments)
        skip_lines: set[int] = set()
        for tok_type, tok_string, tok_start, tok_end, _ in tokens:
            if tok_type == tokenize.COMMENT:
                skip_lines.add(tok_start[0])
            elif tok_type == tokenize.STRING:
                # Mark all lines of a multiline string
                for ln in range(tok_start[0], tok_end[0] + 1):
                    skip_lines.add(ln)

        for i, line in enumerate(source.splitlines(), start=1):
            if i not in skip_lines:
                code_lines.append(line)
    except tokenize.TokenizeError:
        # Fallback: just strip obvious comment lines
        for line in source.splitlines():
            stripped = line.strip()
            if not stripped.startswith("#") and not stripped.startswith('"""') and not stripped.startswith("'''"):
                code_lines.append(line)

    return "\n".join(code_lines)


class TestGatewayActionEnum:
    """Tests for GatewayAction enum validation."""

    def test_start_is_valid_action(self):
        """GatewayAction.START exists with value 'start'."""
        from app.models.gateway import GatewayAction
        assert GatewayAction.START.value == "start"

    def test_stop_is_valid_action(self):
        """GatewayAction.STOP exists with value 'stop'."""
        from app.models.gateway import GatewayAction
        assert GatewayAction.STOP.value == "stop"

    def test_restart_is_valid_action(self):
        """GatewayAction.RESTART exists with value 'restart'."""
        from app.models.gateway import GatewayAction
        assert GatewayAction.RESTART.value == "restart"

    def test_enum_has_exactly_three_members(self):
        """GatewayAction enum has exactly 3 members (start/stop/restart only)."""
        from app.models.gateway import GatewayAction
        assert len(list(GatewayAction)) == 3

    def test_delete_is_not_valid_action(self):
        """'delete' is not a valid GatewayAction value."""
        from app.models.gateway import GatewayAction
        with pytest.raises(ValueError):
            GatewayAction("delete")

    def test_shell_injection_is_not_valid_action(self):
        """Shell injection string is not a valid GatewayAction value."""
        from app.models.gateway import GatewayAction
        with pytest.raises(ValueError):
            GatewayAction("start; rm -rf /")

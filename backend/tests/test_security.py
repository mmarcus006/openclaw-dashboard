"""Security-critical tests for OpenClaw Dashboard backend.

Tests R5 (Host validation), R6 (subprocess exec), R7 (ETag concurrency), and
general sandboxing / path traversal prevention.

These tests MUST all pass. No security test may be skipped because
"it's localhost only".
"""

import io
import re
import tokenize
import pytest
from httpx import ASGITransport, AsyncClient
from pathlib import Path


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _extract_code_lines(source: str) -> str:
    """Return only non-comment, non-docstring lines from Python source.

    Used by grep-style security tests so we don't false-positive on comments
    like ``# NEVER use create_subprocess_shell`` which appear in docstrings.

    Args:
        source: Full Python source as a string.

    Returns:
        Concatenated string of code lines only.
    """
    code_lines = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
        skip_lines: set[int] = set()
        for tok_type, tok_string, tok_start, tok_end, _ in tokens:
            if tok_type == tokenize.COMMENT:
                skip_lines.add(tok_start[0])
            elif tok_type == tokenize.STRING:
                for ln in range(tok_start[0], tok_end[0] + 1):
                    skip_lines.add(ln)
        for i, line in enumerate(source.splitlines(), start=1):
            if i not in skip_lines:
                code_lines.append(line)
    except tokenize.TokenizeError:
        for line in source.splitlines():
            stripped = line.strip()
            if not stripped.startswith("#") and '"""' not in stripped and "'''" not in stripped:
                code_lines.append(line)
    return "\n".join(code_lines)


# ---------------------------------------------------------------------------
# R5: Host Header Validation — DNS Rebinding Protection
# ---------------------------------------------------------------------------

class TestHostHeaderValidation:
    """Verify HostValidationMiddleware rejects non-localhost Host headers (R5)."""

    async def _client_with_host(self, host: str, mock_openclaw_home, test_settings,
                                 file_service, agent_service, config_service, gateway_service):
        """Create an AsyncClient with a custom Host header."""
        from app.main import create_app
        from app.dependencies import (
            get_agent_service, get_config_service, get_file_service,
            get_gateway_service, get_settings,
        )
        app = create_app()
        app.dependency_overrides[get_settings] = lambda: test_settings
        app.dependency_overrides[get_file_service] = lambda: file_service
        app.dependency_overrides[get_agent_service] = lambda: agent_service
        app.dependency_overrides[get_config_service] = lambda: config_service
        app.dependency_overrides[get_gateway_service] = lambda: gateway_service
        return AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
            headers={"Host": host},
        )

    async def test_localhost_host_header_allowed(
        self, mock_openclaw_home, test_settings, file_service, agent_service,
        config_service, gateway_service
    ):
        """Host: localhost is allowed — returns 200 from /api/health."""
        async with await self._client_with_host(
            "localhost", mock_openclaw_home, test_settings, file_service,
            agent_service, config_service, gateway_service
        ) as client:
            response = await client.get("/api/health")
        assert response.status_code == 200

    async def test_localhost_with_port_allowed(
        self, mock_openclaw_home, test_settings, file_service, agent_service,
        config_service, gateway_service
    ):
        """Host: localhost:8400 is allowed."""
        async with await self._client_with_host(
            "localhost:8400", mock_openclaw_home, test_settings, file_service,
            agent_service, config_service, gateway_service
        ) as client:
            response = await client.get("/api/health")
        assert response.status_code == 200

    async def test_127_0_0_1_host_allowed(
        self, mock_openclaw_home, test_settings, file_service, agent_service,
        config_service, gateway_service
    ):
        """Host: 127.0.0.1 is allowed."""
        async with await self._client_with_host(
            "127.0.0.1", mock_openclaw_home, test_settings, file_service,
            agent_service, config_service, gateway_service
        ) as client:
            response = await client.get("/api/health")
        assert response.status_code == 200

    async def test_127_0_0_1_with_port_allowed(
        self, mock_openclaw_home, test_settings, file_service, agent_service,
        config_service, gateway_service
    ):
        """Host: 127.0.0.1:8400 is allowed."""
        async with await self._client_with_host(
            "127.0.0.1:8400", mock_openclaw_home, test_settings, file_service,
            agent_service, config_service, gateway_service
        ) as client:
            response = await client.get("/api/health")
        assert response.status_code == 200

    async def test_evil_com_host_blocked(
        self, mock_openclaw_home, test_settings, file_service, agent_service,
        config_service, gateway_service
    ):
        """Host: evil.com is rejected with 403 (DNS rebinding prevention)."""
        async with await self._client_with_host(
            "evil.com", mock_openclaw_home, test_settings, file_service,
            agent_service, config_service, gateway_service
        ) as client:
            response = await client.get("/api/health")
        assert response.status_code == 403

    async def test_evil_com_with_port_blocked(
        self, mock_openclaw_home, test_settings, file_service, agent_service,
        config_service, gateway_service
    ):
        """Host: evil.com:8400 is rejected with 403."""
        async with await self._client_with_host(
            "evil.com:8400", mock_openclaw_home, test_settings, file_service,
            agent_service, config_service, gateway_service
        ) as client:
            response = await client.get("/api/health")
        assert response.status_code == 403

    async def test_attacker_domain_blocked(
        self, mock_openclaw_home, test_settings, file_service, agent_service,
        config_service, gateway_service
    ):
        """Host: attacker.localhost.evil.com is rejected with 403."""
        async with await self._client_with_host(
            "attacker.localhost.evil.com", mock_openclaw_home, test_settings,
            file_service, agent_service, config_service, gateway_service
        ) as client:
            response = await client.get("/api/health")
        assert response.status_code == 403

    async def test_invalid_host_error_envelope(
        self, mock_openclaw_home, test_settings, file_service, agent_service,
        config_service, gateway_service
    ):
        """Rejected host returns standard error envelope with INVALID_HOST code."""
        async with await self._client_with_host(
            "evil.com", mock_openclaw_home, test_settings, file_service,
            agent_service, config_service, gateway_service
        ) as client:
            response = await client.get("/api/health")
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INVALID_HOST"

    async def test_host_header_middleware_blocks_config_endpoint(
        self, mock_openclaw_home, test_settings, file_service, agent_service,
        config_service, gateway_service
    ):
        """DNS rebinding attack on /api/config is blocked (the highest-risk endpoint)."""
        async with await self._client_with_host(
            "evil.com", mock_openclaw_home, test_settings, file_service,
            agent_service, config_service, gateway_service
        ) as client:
            response = await client.get("/api/config")
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# R6: Subprocess Security — Never create_subprocess_shell
# ---------------------------------------------------------------------------

class TestSubprocessSecurity:
    """Verify no source file uses create_subprocess_shell (R6)."""

    def test_no_subprocess_shell_in_gateway_service(self):
        """create_subprocess_shell must not be CALLED in gateway_service.py.

        Note: The string may appear in comments/docstrings. We check code lines only.
        """
        source_file = Path(__file__).parent.parent / "app" / "services" / "gateway_service.py"
        code_lines = _extract_code_lines(source_file.read_text())
        assert "create_subprocess_shell" not in code_lines, (
            "SECURITY VIOLATION: create_subprocess_shell called in gateway_service.py"
        )

    def test_create_subprocess_exec_used_in_gateway_service(self):
        """create_subprocess_exec must be used in gateway_service.py."""
        source_file = Path(__file__).parent.parent / "app" / "services" / "gateway_service.py"
        source = source_file.read_text()
        assert "create_subprocess_exec" in source

    def test_no_subprocess_shell_in_any_app_file(self):
        """create_subprocess_shell must not be CALLED anywhere in app/.

        Comment lines (including docstrings warning against usage) are excluded.
        """
        app_dir = Path(__file__).parent.parent / "app"
        violations = []
        for py_file in app_dir.rglob("*.py"):
            code_lines = _extract_code_lines(py_file.read_text())
            if "create_subprocess_shell" in code_lines:
                violations.append(str(py_file))
        assert violations == [], (
            f"SECURITY VIOLATION: create_subprocess_shell found in: {violations}"
        )

    def test_no_os_system_in_gateway_service(self):
        """os.system() must not be used in gateway_service.py."""
        source_file = Path(__file__).parent.parent / "app" / "services" / "gateway_service.py"
        source = source_file.read_text()
        assert "os.system(" not in source

    def test_no_subprocess_run_shell_true_in_any_app_file(self):
        """subprocess.run() with shell=True must not appear in app/."""
        app_dir = Path(__file__).parent.parent / "app"
        for py_file in app_dir.rglob("*.py"):
            source = py_file.read_text()
            # Very basic check — catches the obvious pattern
            assert "shell=True" not in source, (
                f"shell=True found in {py_file} — dangerous subprocess usage"
            )


# ---------------------------------------------------------------------------
# R7: ETag / Optimistic Concurrency
# ---------------------------------------------------------------------------

class TestETagConcurrency:
    """Verify ETag-based optimistic concurrency prevents silent overwrites (R7)."""

    async def test_etag_mismatch_returns_409(self, async_client: AsyncClient):
        """Concurrent write with stale ETag returns 409 Conflict."""
        # Write initial file
        await async_client.put(
            "/api/agents/main/files?path=CONCURRENCY_TEST.md",
            json={"content": "v1"},
        )

        # Get ETag
        read_resp = await async_client.get(
            "/api/agents/main/files?path=CONCURRENCY_TEST.md"
        )
        etag1 = read_resp.headers["etag"]

        # Overwrite outside (simulating another process)
        await async_client.put(
            "/api/agents/main/files?path=CONCURRENCY_TEST.md",
            json={"content": "v2 - written by another process"},
        )

        # Now try to save with the OLD etag — should 409
        response = await async_client.put(
            "/api/agents/main/files?path=CONCURRENCY_TEST.md",
            headers={"if-match": etag1},
            json={"content": "v1 overwrite attempt"},
        )
        assert response.status_code == 409

    async def test_etag_matches_prevents_data_loss(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """Writing with the correct current ETag succeeds and doesn't lose data."""
        await async_client.put(
            "/api/agents/main/files?path=NO_LOSS_TEST.md",
            json={"content": "original"},
        )
        read_resp = await async_client.get(
            "/api/agents/main/files?path=NO_LOSS_TEST.md"
        )
        current_etag = read_resp.headers["etag"]

        write_resp = await async_client.put(
            "/api/agents/main/files?path=NO_LOSS_TEST.md",
            headers={"if-match": current_etag},
            json={"content": "updated safely"},
        )
        assert write_resp.status_code == 200
        on_disk = (mock_openclaw_home / "workspace" / "NO_LOSS_TEST.md").read_text()
        assert on_disk == "updated safely"

    async def test_file_service_etag_mismatch_raises_error(
        self, file_service, mock_openclaw_home: Path
    ):
        """FileService.write_file raises ETagMismatchError on stale ETag (unit test)."""
        from app.middleware.error_handler import ETagMismatchError

        target = mock_openclaw_home / "workspace" / "ETAG_UNIT_TEST.md"
        target.write_text("original content")

        # Get real etag
        real_etag = file_service.compute_etag(target)

        # Modify file externally
        target.write_text("modified by another process")

        # Now try to write with the OLD (stale) etag
        with pytest.raises(ETagMismatchError):
            await file_service.write_file(target, "my update", if_match=real_etag)

    async def test_config_etag_mismatch_returns_409(self, async_client: AsyncClient):
        """Config write with stale ETag returns 409.

        We change the config content between writes so the SHA-1 content hash changes,
        guaranteeing a new ETag regardless of write timing.
        """
        # GET the current config and etag
        get_resp = await async_client.get("/api/config")
        config = get_resp.json()["config"]
        original_etag = get_resp.json()["etag"]

        # First write: change the content so the SHA-1 content hash changes
        config_v2 = dict(config)
        config_v2["_etag_test_marker"] = "x" * 200  # ensures size change

        first_write = await async_client.put(
            "/api/config",
            json={"config": config_v2},
            headers={"if-match": f'"{original_etag}"'},
        )
        assert first_write.status_code == 200
        new_etag = first_write.json()["etag"]

        # Sanity: the ETag MUST have changed (different size)
        assert new_etag != original_etag, (
            "ETag did not change after write — test precondition not met. "
            "The size of the written config must be different from the original."
        )

        # Second write with the now-stale original ETag — must 409
        response = await async_client.put(
            "/api/config",
            json={"config": config_v2},
            headers={"if-match": f'"{original_etag}"'},  # stale
        )
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# File Sandboxing
# ---------------------------------------------------------------------------

class TestFileSandboxing:
    """Verify FileService._check_path prevents escaping the sandbox."""

    def test_path_inside_sandbox_allowed(
        self, file_service, mock_openclaw_home: Path
    ):
        """A path inside OPENCLAW_HOME resolves without error."""
        target = mock_openclaw_home / "workspace" / "AGENTS.md"
        # Should not raise
        result = file_service._check_path(target, write=False)
        assert result == target.resolve()

    def test_path_outside_sandbox_raises_permission_error(
        self, file_service, mock_openclaw_home: Path
    ):
        """A path outside OPENCLAW_HOME raises PermissionError."""
        outside = Path("/etc/passwd")
        with pytest.raises(PermissionError):
            file_service._check_path(outside, write=False)

    def test_symlink_to_outside_sandbox_blocked(
        self, file_service, mock_openclaw_home: Path
    ):
        """A symlink pointing outside OPENCLAW_HOME raises PermissionError."""
        workspace = mock_openclaw_home / "workspace"
        symlink = workspace / "evil_symlink"
        try:
            symlink.symlink_to(Path("/tmp"))
        except OSError:
            pytest.skip("Cannot create symlink in this environment")

        with pytest.raises(PermissionError):
            file_service._check_path(symlink, write=False)

    def test_path_traversal_via_resolved_path_blocked(
        self, file_service, mock_openclaw_home: Path
    ):
        """Path that traverses above OPENCLAW_HOME parent is blocked."""
        malicious = mock_openclaw_home / "workspace" / ".." / ".." / ".." / "etc" / "passwd"
        with pytest.raises(PermissionError):
            file_service._check_path(malicious, write=False)


# ---------------------------------------------------------------------------
# CORS Security
# ---------------------------------------------------------------------------

class TestCORSPolicy:
    """Verify CORS is configured to only allow localhost:5173 (not *)."""

    async def test_cors_preflight_from_localhost_5173_allowed(
        self, async_client: AsyncClient
    ):
        """OPTIONS preflight from http://localhost:5173 includes CORS allow header."""
        response = await async_client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Should not be blocked — CORS headers present
        assert response.status_code in (200, 204)
        # The response should echo back the allowed origin
        allow_origin = response.headers.get("access-control-allow-origin", "")
        assert allow_origin == "http://localhost:5173" or allow_origin == "*"

    async def test_cors_preflight_from_evil_origin_blocked(
        self, async_client: AsyncClient
    ):
        """OPTIONS preflight from http://evil.com does NOT get wildcard CORS."""
        response = await async_client.options(
            "/api/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        allow_origin = response.headers.get("access-control-allow-origin", "")
        assert allow_origin != "*", "CORS must never be * — this allows any origin!"
        assert "evil.com" not in allow_origin

    def test_cors_never_wildcard_in_main_py(self):
        """main.py must not use allow_origins=['*'] or allow_origins=["*"]."""
        main_file = Path(__file__).parent.parent / "app" / "main.py"
        source = main_file.read_text()
        # Specifically check allow_origins is not set to wildcard
        # Note: allow_headers=["*"] is acceptable — we check origins specifically
        wildcard_origins = re.search(r'allow_origins\s*=\s*\[["\']\*["\']\]', source)
        assert wildcard_origins is None, (
            "CORS allow_origins must not be ['*'] — DNS rebinding risk (REVIEW.md §3.2)"
        )

    def test_cors_configured_for_localhost_only_in_main_py(self):
        """main.py configures CORS for localhost:5173 only."""
        main_file = Path(__file__).parent.parent / "app" / "main.py"
        source = main_file.read_text()
        assert "localhost:5173" in source


# ---------------------------------------------------------------------------
# Error Envelope
# ---------------------------------------------------------------------------

class TestErrorEnvelope:
    """Verify all error responses use the standard error envelope."""

    async def test_404_uses_error_envelope(self, async_client: AsyncClient):
        """404 response has 'error' object with code, message, detail, timestamp."""
        response = await async_client.get("/api/agents/definitely_nonexistent_agent_xyz")
        data = response.json()
        assert "error" in data
        error = data["error"]
        assert "code" in error
        assert "message" in error
        assert "timestamp" in error

    async def test_422_uses_error_envelope(self, async_client: AsyncClient):
        """422 (validation error) has 'error' object."""
        response = await async_client.post("/api/gateway/invalid_action")
        data = response.json()
        assert "error" in data

    async def test_403_from_host_validation_uses_error_envelope(
        self, mock_openclaw_home, test_settings, file_service, agent_service,
        config_service, gateway_service
    ):
        """403 from host validation uses the standard error envelope."""
        from app.main import create_app
        from app.dependencies import (
            get_agent_service, get_config_service, get_file_service,
            get_gateway_service, get_settings,
        )
        app = create_app()
        app.dependency_overrides[get_settings] = lambda: test_settings
        app.dependency_overrides[get_file_service] = lambda: file_service
        app.dependency_overrides[get_agent_service] = lambda: agent_service
        app.dependency_overrides[get_config_service] = lambda: config_service
        app.dependency_overrides[get_gateway_service] = lambda: gateway_service

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
            headers={"Host": "evil.com"},
        ) as client:
            response = await client.get("/api/health")

        data = response.json()
        assert "error" in data
        error = data["error"]
        assert "code" in error
        assert "message" in error
        assert "timestamp" in error

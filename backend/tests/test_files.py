"""Tests for agent file read/write endpoints with ETag concurrency control (R7).

Covers:
  - GET /api/agents/{id}/files?path=X  returns content + ETag header
  - PUT /api/agents/{id}/files?path=X  with correct If-Match succeeds
  - PUT with wrong If-Match → 409 Conflict
  - PUT without If-Match → succeeds (If-Match is optional for new files)
  - File content actually written to disk after PUT
  - Nonexistent file → 404
  - Path traversal blocked → 400/403
  - Null byte injection → 400/422
  - Double-encoded traversal → 400/403
  - Language detection from file extension
"""

import pytest
from httpx import AsyncClient
from pathlib import Path


class TestFileRead:
    """Tests for GET /api/agents/{id}/files?path=X."""

    async def test_read_existing_file_returns_200(self, async_client: AsyncClient):
        """Reading AGENTS.md from main workspace returns 200."""
        response = await async_client.get("/api/agents/main/files?path=AGENTS.md")
        assert response.status_code == 200

    async def test_read_returns_content(self, async_client: AsyncClient):
        """Response body includes a 'content' field with the file text."""
        response = await async_client.get("/api/agents/main/files?path=AGENTS.md")
        data = response.json()
        assert "content" in data
        assert "AGENTS.md" in data["content"]

    async def test_read_returns_etag_header(self, async_client: AsyncClient):
        """Response includes an ETag header."""
        response = await async_client.get("/api/agents/main/files?path=AGENTS.md")
        assert "etag" in response.headers

    async def test_read_etag_format(self, async_client: AsyncClient):
        """ETag header is a 16-character lowercase hex SHA-1 hash (quoted)."""
        response = await async_client.get("/api/agents/main/files?path=AGENTS.md")
        etag = response.headers["etag"].strip('"')
        # Format: 16 lowercase hex characters (first 16 chars of SHA-1)
        assert len(etag) == 16, f"Expected 16-char hex ETag, got {etag!r}"
        assert all(c in "0123456789abcdef" for c in etag), f"ETag is not lowercase hex: {etag!r}"

    async def test_read_returns_path_field(self, async_client: AsyncClient):
        """Response body includes a 'path' field matching the requested path."""
        response = await async_client.get("/api/agents/main/files?path=AGENTS.md")
        assert response.json()["path"] == "AGENTS.md"

    async def test_read_returns_size_field(self, async_client: AsyncClient):
        """Response body includes a 'size' field > 0."""
        response = await async_client.get("/api/agents/main/files?path=AGENTS.md")
        assert response.json()["size"] > 0

    async def test_read_returns_language_markdown(self, async_client: AsyncClient):
        """AGENTS.md is detected as 'markdown' language."""
        response = await async_client.get("/api/agents/main/files?path=AGENTS.md")
        assert response.json()["language"] == "markdown"

    async def test_read_nonexistent_file_returns_404(self, async_client: AsyncClient):
        """Reading a file that doesn't exist returns 404."""
        response = await async_client.get("/api/agents/main/files?path=NONEXISTENT.md")
        assert response.status_code == 404

    async def test_read_nonexistent_file_has_error_envelope(self, async_client: AsyncClient):
        """404 response uses the standard error envelope."""
        response = await async_client.get("/api/agents/main/files?path=NONEXISTENT.md")
        assert "error" in response.json()

    async def test_read_coder_agent_file(self, async_client: AsyncClient):
        """Can read files from a non-main agent workspace."""
        response = await async_client.get("/api/agents/coder/files?path=AGENTS.md")
        assert response.status_code == 200

    async def test_read_soul_md(self, async_client: AsyncClient):
        """Reading SOUL.md returns the soul file content."""
        response = await async_client.get("/api/agents/main/files?path=SOUL.md")
        assert response.status_code == 200
        assert "COS" in response.json()["content"]


class TestFileWrite:
    """Tests for PUT /api/agents/{id}/files?path=X."""

    async def test_write_new_file_without_if_match_succeeds(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """Writing a new file (no If-Match) succeeds with 200."""
        response = await async_client.put(
            "/api/agents/main/files?path=TEST_NEW.md",
            json={"content": "# New file"},
        )
        assert response.status_code == 200

    async def test_write_new_file_creates_on_disk(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """Content written via PUT appears on disk."""
        content = "# Test write content\nWritten by tests."
        await async_client.put(
            "/api/agents/main/files?path=DISK_TEST.md",
            json={"content": content},
        )
        written = (mock_openclaw_home / "workspace" / "DISK_TEST.md").read_text()
        assert written == content

    async def test_write_returns_new_etag(
        self, async_client: AsyncClient
    ):
        """PUT response includes a new etag field."""
        response = await async_client.put(
            "/api/agents/main/files?path=ETAG_TEST.md",
            json={"content": "# ETag test"},
        )
        data = response.json()
        assert "etag" in data
        assert data["etag"]

    async def test_write_with_correct_if_match_succeeds(
        self, async_client: AsyncClient
    ):
        """PUT with correct If-Match header succeeds with 200."""
        # First write to create the file
        create_resp = await async_client.put(
            "/api/agents/main/files?path=IFMATCH_TEST.md",
            json={"content": "Initial content"},
        )
        assert create_resp.status_code == 200
        etag = create_resp.json()["etag"]

        # Second write using the ETag from the first write
        update_resp = await async_client.put(
            "/api/agents/main/files?path=IFMATCH_TEST.md",
            headers={"if-match": f'"{etag}"'},
            json={"content": "Updated content"},
        )
        assert update_resp.status_code == 200

    async def test_write_with_correct_if_match_updates_disk(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """PUT with correct If-Match actually updates the file on disk."""
        await async_client.put(
            "/api/agents/main/files?path=UPDATE_TEST.md",
            json={"content": "Version 1"},
        )
        read_resp = await async_client.get("/api/agents/main/files?path=UPDATE_TEST.md")
        etag = read_resp.headers["etag"]

        await async_client.put(
            "/api/agents/main/files?path=UPDATE_TEST.md",
            headers={"if-match": etag},
            json={"content": "Version 2"},
        )
        on_disk = (mock_openclaw_home / "workspace" / "UPDATE_TEST.md").read_text()
        assert on_disk == "Version 2"

    async def test_write_with_wrong_if_match_returns_409(
        self, async_client: AsyncClient
    ):
        """PUT with incorrect If-Match header returns 409 Conflict."""
        # Create the file first
        await async_client.put(
            "/api/agents/main/files?path=CONFLICT_TEST.md",
            json={"content": "Initial"},
        )
        # Now send wrong ETag
        response = await async_client.put(
            "/api/agents/main/files?path=CONFLICT_TEST.md",
            headers={"if-match": '"0:0"'},  # clearly wrong
            json={"content": "Should fail"},
        )
        assert response.status_code == 409

    async def test_write_conflict_has_error_envelope(
        self, async_client: AsyncClient
    ):
        """409 response includes the standard error envelope with CONFLICT code."""
        await async_client.put(
            "/api/agents/main/files?path=CONFLICT_ENVELOPE.md",
            json={"content": "Base"},
        )
        response = await async_client.put(
            "/api/agents/main/files?path=CONFLICT_ENVELOPE.md",
            headers={"if-match": '"0:0"'},
            json={"content": "Conflicted"},
        )
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "CONFLICT"

    async def test_write_conflict_includes_current_etag(
        self, async_client: AsyncClient
    ):
        """409 response detail includes current_etag so client can retry."""
        await async_client.put(
            "/api/agents/main/files?path=CURRENT_ETAG_TEST.md",
            json={"content": "Base"},
        )
        response = await async_client.put(
            "/api/agents/main/files?path=CURRENT_ETAG_TEST.md",
            headers={"if-match": '"0:0"'},
            json={"content": "Conflicted"},
        )
        detail = response.json()["error"]["detail"]
        assert "current_etag" in detail

    async def test_write_missing_content_returns_400(
        self, async_client: AsyncClient
    ):
        """PUT with no 'content' key in body returns 400."""
        response = await async_client.put(
            "/api/agents/main/files?path=NO_CONTENT.md",
            json={"wrong_key": "data"},
        )
        assert response.status_code == 400


class TestPathSecurity:
    """Tests for path traversal and injection attacks."""

    async def test_path_traversal_dotdot_blocked_read(
        self, async_client: AsyncClient
    ):
        """GET with ../../etc/passwd path is blocked (400 or 403)."""
        response = await async_client.get(
            "/api/agents/main/files?path=../../etc/passwd"
        )
        assert response.status_code in (400, 403)

    async def test_path_traversal_dotdot_blocked_write(
        self, async_client: AsyncClient
    ):
        """PUT with ../../etc/shadow path is blocked."""
        response = await async_client.put(
            "/api/agents/main/files?path=../../etc/shadow",
            json={"content": "evil"},
        )
        assert response.status_code in (400, 403)

    async def test_path_traversal_deep_blocked(
        self, async_client: AsyncClient
    ):
        """GET with ../../../etc/passwd is blocked."""
        response = await async_client.get(
            "/api/agents/main/files?path=../../../etc/passwd"
        )
        assert response.status_code in (400, 403)

    async def test_path_traversal_subdirectory_blocked(
        self, async_client: AsyncClient
    ):
        """GET with subdir/../../../etc/passwd is blocked."""
        response = await async_client.get(
            "/api/agents/main/files?path=subdir/../../../etc/passwd"
        )
        assert response.status_code in (400, 403)

    async def test_double_encoded_traversal_blocked_read(
        self, async_client: AsyncClient
    ):
        """Double URL-encoded traversal (%252e%252e) is blocked."""
        response = await async_client.get(
            "/api/agents/main/files?path=%252e%252e%252fetc%252fpasswd"
        )
        # httpx will decode this before sending; the path won't have ../
        # so we expect a 404 (path not found in sandbox) or 403
        assert response.status_code in (400, 403, 404)

    async def test_null_byte_injection_blocked(
        self, async_client: AsyncClient
    ):
        """Path with null byte is blocked or treated as not-found.

        422 is also acceptable — Pydantic/FastAPI rejects the malformed query param
        before it reaches any file code, which is the correct secure behavior.
        """
        response = await async_client.get(
            "/api/agents/main/files",
            params={"path": "AGENTS.md\x00.txt"},
        )
        # Must NOT be 200 — any rejection code (400, 403, 404, 422) is fine
        assert response.status_code in (400, 403, 404, 422)

    async def test_absolute_path_outside_sandbox_blocked(
        self, async_client: AsyncClient
    ):
        """Absolute path to /etc/passwd is blocked."""
        response = await async_client.get(
            "/api/agents/main/files?path=/etc/passwd"
        )
        assert response.status_code in (400, 403, 404)


class TestSymlinkSandbox:
    """Tests for symlink traversal prevention (R3.3 from REVIEW.md)."""

    async def test_symlink_outside_sandbox_blocked(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """A symlink in the workspace pointing outside the sandbox is blocked."""
        import os
        workspace = mock_openclaw_home / "workspace"
        # Create a symlink pointing to /tmp (outside sandbox)
        symlink_path = workspace / "evil_link.md"
        target = Path("/tmp")  # outside openclaw home
        try:
            symlink_path.symlink_to(target)
        except OSError:
            pytest.skip("Cannot create symlink")

        response = await async_client.get(
            "/api/agents/main/files?path=evil_link.md"
        )
        # Resolving the symlink to /tmp should fail sandbox check
        assert response.status_code in (403, 404)

    async def test_symlink_to_etc_passwd_blocked(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """A symlink pointing to /etc/passwd is blocked."""
        workspace = mock_openclaw_home / "workspace"
        symlink_path = workspace / "passwd_link"
        try:
            symlink_path.symlink_to(Path("/etc/passwd"))
        except OSError:
            pytest.skip("Cannot create symlink")

        response = await async_client.get(
            "/api/agents/main/files?path=passwd_link"
        )
        assert response.status_code in (403, 404)


class TestLanguageDetection:
    """Tests for file language detection."""

    @pytest.mark.parametrize("filename,expected_language", [
        ("test.md", "markdown"),
        ("test.py", "python"),
        ("test.json", "json"),
        ("test.ts", "typescript"),
        ("test.js", "javascript"),
        ("test.yml", "yaml"),
        ("test.yaml", "yaml"),
        ("test.sh", "shell"),
        ("test.txt", "plaintext"),
        ("test.unknown_ext", "plaintext"),
    ])
    def test_language_detection(
        self, file_service, filename: str, expected_language: str
    ):
        """Detect Monaco language from file extension."""
        result = file_service.detect_language(filename)
        assert result == expected_language

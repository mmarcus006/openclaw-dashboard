"""Tests for /api/config/* endpoints.

Covers:
  - GET /api/config returns JSON with secrets redacted
  - Redacted fields contain __REDACTED__, not real values
  - PUT /api/config creates backup before writing
  - PUT /api/config with correct If-Match works
  - PUT /api/config preserves __REDACTED__ values (doesn't write sentinel to disk)
  - PUT /api/config with wrong If-Match → 409
  - POST /api/config/validate accepts valid JSON
  - POST /api/config/validate rejects invalid structures
  - Backup rotation: after 11 writes, only 10 backup files exist
"""

import json
from pathlib import Path

from httpx import AsyncClient


class TestConfigRead:
    """Tests for GET /api/config."""

    async def test_get_config_returns_200(self, async_client: AsyncClient):
        """GET /api/config returns HTTP 200."""
        response = await async_client.get("/api/config")
        assert response.status_code == 200

    async def test_get_config_returns_config_dict(self, async_client: AsyncClient):
        """Response includes a 'config' key with a dict."""
        response = await async_client.get("/api/config")
        data = response.json()
        assert "config" in data
        assert isinstance(data["config"], dict)

    async def test_get_config_returns_etag(self, async_client: AsyncClient):
        """Response includes an 'etag' field."""
        response = await async_client.get("/api/config")
        data = response.json()
        assert "etag" in data
        assert data["etag"]

    async def test_get_config_redacts_api_key(self, async_client: AsyncClient):
        """API key values are replaced with __REDACTED__."""
        response = await async_client.get("/api/config")
        config = response.json()["config"]
        api = config.get("api", {})
        # openai_api_key contains "key" — should be redacted
        assert api.get("openai_api_key") == "__REDACTED__"

    async def test_get_config_redacts_token(self, async_client: AsyncClient):
        """Token values are replaced with __REDACTED__."""
        response = await async_client.get("/api/config")
        config = response.json()["config"]
        api = config.get("api", {})
        # anthropic_token contains "token" — should be redacted
        assert api.get("anthropic_token") == "__REDACTED__"

    async def test_get_config_does_not_leak_real_secret(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """The real secret value 'sk-test-secret-key' does not appear in the response."""
        response = await async_client.get("/api/config")
        response_text = response.text
        assert "sk-test-secret-key" not in response_text
        assert "ant-test-token" not in response_text

    async def test_get_config_non_secret_values_not_redacted(
        self, async_client: AsyncClient
    ):
        """Non-secret values (like gateway port) are not redacted."""
        response = await async_client.get("/api/config")
        config = response.json()["config"]
        # gateway.port = 3000 (not a secret key)
        assert config.get("gateway", {}).get("port") == 3000

    async def test_get_config_404_when_missing(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """GET /api/config returns 404 when openclaw.json is missing."""
        config_path = mock_openclaw_home / "openclaw.json"
        config_path.unlink()
        response = await async_client.get("/api/config")
        assert response.status_code == 404


class TestConfigWrite:
    """Tests for PUT /api/config."""

    async def _get_config_with_etag(self, client: AsyncClient) -> tuple[dict, str]:
        """Helper: get config and return (config_dict, etag_string)."""
        resp = await client.get("/api/config")
        data = resp.json()
        return data["config"], data["etag"]

    async def test_put_config_returns_200(self, async_client: AsyncClient):
        """PUT /api/config returns 200."""
        config, etag = await self._get_config_with_etag(async_client)
        response = await async_client.put(
            "/api/config",
            json={"config": config},
            headers={"if-match": f'"{etag}"'},
        )
        assert response.status_code == 200

    async def test_put_config_with_wrong_etag_returns_409(
        self, async_client: AsyncClient
    ):
        """PUT /api/config with wrong If-Match returns 409."""
        config, _ = await self._get_config_with_etag(async_client)
        response = await async_client.put(
            "/api/config",
            json={"config": config},
            headers={"if-match": '"0:0"'},
        )
        assert response.status_code == 409

    async def test_put_config_conflict_has_error_envelope(
        self, async_client: AsyncClient
    ):
        """409 response has CONFLICT error code in envelope."""
        config, _ = await self._get_config_with_etag(async_client)
        response = await async_client.put(
            "/api/config",
            json={"config": config},
            headers={"if-match": '"0:0"'},
        )
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "CONFLICT"

    async def test_put_config_creates_backup(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """PUT creates a backup file in the same directory as openclaw.json."""
        config, etag = await self._get_config_with_etag(async_client)
        await async_client.put(
            "/api/config",
            json={"config": config},
            headers={"if-match": f'"{etag}"'},
        )
        backups = list(mock_openclaw_home.glob("openclaw.json.bak.*"))
        assert len(backups) >= 1

    async def test_put_config_preserves_redacted_secret(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """Sending __REDACTED__ for a secret preserves the original value on disk."""
        # GET config — secrets will be __REDACTED__ in response
        config, etag = await self._get_config_with_etag(async_client)
        # Confirm the api section has redacted values
        assert config["api"]["openai_api_key"] == "__REDACTED__"

        # PUT back with __REDACTED__ still in place
        response = await async_client.put(
            "/api/config",
            json={"config": config},
            headers={"if-match": f'"{etag}"'},
        )
        assert response.status_code == 200

        # Verify the real secret is preserved on disk (not __REDACTED__)
        on_disk = json.loads((mock_openclaw_home / "openclaw.json").read_text())
        assert on_disk["api"]["openai_api_key"] == "sk-test-secret-key"
        assert on_disk["api"]["anthropic_token"] == "ant-test-token"

    async def test_put_config_does_not_write_redacted_sentinel_to_disk(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """__REDACTED__ is never written literally to disk."""
        config, etag = await self._get_config_with_etag(async_client)
        await async_client.put(
            "/api/config",
            json={"config": config},
            headers={"if-match": f'"{etag}"'},
        )
        disk_content = (mock_openclaw_home / "openclaw.json").read_text()
        assert "__REDACTED__" not in disk_content

    async def test_put_config_updates_disk(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """PUT actually writes new values to disk."""
        config, etag = await self._get_config_with_etag(async_client)
        # Add a new non-secret key
        config["test_key_written_by_test"] = "hello-world"

        await async_client.put(
            "/api/config",
            json={"config": config},
            headers={"if-match": f'"{etag}"'},
        )
        on_disk = json.loads((mock_openclaw_home / "openclaw.json").read_text())
        assert on_disk.get("test_key_written_by_test") == "hello-world"

    async def test_put_config_returns_new_etag(self, async_client: AsyncClient):
        """PUT /api/config response includes a new ETag."""
        config, etag = await self._get_config_with_etag(async_client)
        response = await async_client.put(
            "/api/config",
            json={"config": config},
            headers={"if-match": f'"{etag}"'},
        )
        data = response.json()
        assert "etag" in data

    async def test_put_config_returns_redacted_config(
        self, async_client: AsyncClient
    ):
        """PUT /api/config response returns the config with secrets still redacted."""
        config, etag = await self._get_config_with_etag(async_client)
        response = await async_client.put(
            "/api/config",
            json={"config": config},
            headers={"if-match": f'"{etag}"'},
        )
        data = response.json()
        assert data["config"]["api"]["openai_api_key"] == "__REDACTED__"


class TestBackupRotation:
    """Tests for backup rotation (max 10 backups)."""

    async def test_backup_rotation_keeps_max_10_backups(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """After 11 config writes, only 10 backup files remain."""
        # Perform 11 writes
        for i in range(11):
            resp = await async_client.get("/api/config")
            config = resp.json()["config"]
            etag = resp.json()["etag"]
            config["iteration"] = i
            write_resp = await async_client.put(
                "/api/config",
                json={"config": config},
                headers={"if-match": f'"{etag}"'},
            )
            assert write_resp.status_code == 200

        backups = list(mock_openclaw_home.glob("openclaw.json.bak.*"))
        assert len(backups) <= 10

    async def test_backup_rotation_single_write_creates_one_backup(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """A single write creates exactly one backup file."""
        initial_backups = list(mock_openclaw_home.glob("openclaw.json.bak.*"))
        config, etag = (await async_client.get("/api/config")).json()["config"], \
                       (await async_client.get("/api/config")).json()["etag"]
        await async_client.put(
            "/api/config",
            json={"config": config},
            headers={"if-match": f'"{etag}"'},
        )
        after_backups = list(mock_openclaw_home.glob("openclaw.json.bak.*"))
        assert len(after_backups) == len(initial_backups) + 1


class TestConfigValidate:
    """Tests for POST /api/config/validate."""

    async def test_validate_valid_config_returns_200(self, async_client: AsyncClient):
        """POST /api/config/validate with a valid config returns 200."""
        response = await async_client.post(
            "/api/config/validate",
            json={"config": {"agents": {"defaults": {"model": "test"}}}},
        )
        assert response.status_code == 200

    async def test_validate_valid_config_returns_valid_true(
        self, async_client: AsyncClient
    ):
        """Valid config returns valid=True."""
        response = await async_client.post(
            "/api/config/validate",
            json={"config": {"gateway": {"port": 3000}}},
        )
        assert response.json()["valid"] is True

    async def test_validate_has_errors_and_warnings_fields(
        self, async_client: AsyncClient
    ):
        """Validate response always has 'errors' and 'warnings' lists."""
        response = await async_client.post(
            "/api/config/validate",
            json={"config": {}},
        )
        data = response.json()
        assert "errors" in data
        assert "warnings" in data
        assert isinstance(data["errors"], list)
        assert isinstance(data["warnings"], list)

    async def test_validate_invalid_port_returns_errors(
        self, async_client: AsyncClient
    ):
        """Config with invalid gateway port returns valid=False with errors."""
        response = await async_client.post(
            "/api/config/validate",
            json={"config": {"gateway": {"port": 80}}},  # below 1024
        )
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    async def test_validate_valid_port_returns_no_errors(
        self, async_client: AsyncClient
    ):
        """Config with valid gateway port returns valid=True."""
        response = await async_client.post(
            "/api/config/validate",
            json={"config": {"gateway": {"port": 3000}}},
        )
        data = response.json()
        assert data["valid"] is True

    async def test_validate_non_object_returns_error(
        self, async_client: AsyncClient
    ):
        """Sending a non-dict config returns valid=False or 422."""
        # pydantic will reject non-dict before we even hit validate_config
        response = await async_client.post(
            "/api/config/validate",
            json={"config": [1, 2, 3]},  # list instead of dict
        )
        # Either rejected by pydantic (422) or by validate_config (valid=False)
        assert response.status_code in (200, 422)
        if response.status_code == 200:
            assert response.json()["valid"] is False

    async def test_validate_empty_config_is_valid(
        self, async_client: AsyncClient
    ):
        """An empty config dict is considered valid (no required fields)."""
        response = await async_client.post(
            "/api/config/validate",
            json={"config": {}},
        )
        assert response.json()["valid"] is True


class TestSecretRedaction:
    """Unit tests for the _redact_secrets utility function."""

    def test_redact_secrets_replaces_key_with_redacted(self):
        """Keys containing 'key' are redacted."""
        from app.services.config_service import _redact_secrets
        result = _redact_secrets({"api_key": "secret123"})
        assert result["api_key"] == "__REDACTED__"

    def test_redact_secrets_replaces_token(self):
        """Keys containing 'token' are redacted."""
        from app.services.config_service import _redact_secrets
        result = _redact_secrets({"access_token": "tok-abc"})
        assert result["access_token"] == "__REDACTED__"

    def test_redact_secrets_replaces_secret(self):
        """Keys containing 'secret' are redacted."""
        from app.services.config_service import _redact_secrets
        result = _redact_secrets({"client_secret": "s3cr3t"})
        assert result["client_secret"] == "__REDACTED__"

    def test_redact_secrets_replaces_password(self):
        """Keys containing 'password' are redacted."""
        from app.services.config_service import _redact_secrets
        result = _redact_secrets({"db_password": "pass123"})
        assert result["db_password"] == "__REDACTED__"

    def test_redact_secrets_does_not_redact_non_secret_keys(self):
        """Non-secret keys are not redacted."""
        from app.services.config_service import _redact_secrets
        result = _redact_secrets({"gateway_port": 3000, "log_level": "INFO"})
        assert result["gateway_port"] == 3000
        assert result["log_level"] == "INFO"

    def test_redact_secrets_works_recursively(self):
        """Nested dicts are recursively redacted."""
        from app.services.config_service import _redact_secrets
        result = _redact_secrets({"api": {"openai_key": "sk-secret"}})
        assert result["api"]["openai_key"] == "__REDACTED__"

    def test_restore_redacted_restores_from_original(self):
        """_restore_redacted replaces __REDACTED__ with the original value."""
        from app.services.config_service import _restore_redacted
        incoming = {"api_key": "__REDACTED__", "name": "test"}
        original = {"api_key": "real-secret", "name": "old-test"}
        result = _restore_redacted(incoming, original)
        assert result["api_key"] == "real-secret"
        assert result["name"] == "test"  # non-redacted values from incoming

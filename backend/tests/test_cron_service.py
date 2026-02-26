"""Tests for CronService and GET /api/cron endpoint."""

import json
from pathlib import Path

from httpx import AsyncClient


class TestCronList:
    """Tests for cron job listing."""

    async def test_cron_list_parses_config(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """GET /api/cron returns cron jobs from config."""
        config_path = mock_openclaw_home / "openclaw.json"
        config = json.loads(config_path.read_text())
        config["cron"] = {
            "health-check": {
                "schedule": "*/30 * * * *",
                "enabled": True,
            },
            "backup": {
                "schedule": "0 2 * * *",
                "enabled": False,
            },
        }
        config_path.write_text(json.dumps(config))

        response = await async_client.get("/api/cron")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        names = {j["name"] for j in data["jobs"]}
        assert names == {"health-check", "backup"}

        health = next(j for j in data["jobs"] if j["name"] == "health-check")
        assert health["schedule"] == "*/30 * * * *"
        assert health["enabled"] is True
        assert health["next_run"] is not None
        assert health["error"] is None

        backup = next(j for j in data["jobs"] if j["name"] == "backup")
        assert backup["enabled"] is False

    async def test_malformed_cron_expression(
        self, async_client: AsyncClient, mock_openclaw_home: Path
    ):
        """Malformed cron expression returns error field, doesn't crash the list."""
        config_path = mock_openclaw_home / "openclaw.json"
        config = json.loads(config_path.read_text())
        config["cron"] = {
            "good-job": {
                "schedule": "0 * * * *",
                "enabled": True,
            },
            "bad-job": {
                "schedule": "not a cron",
                "enabled": True,
            },
        }
        config_path.write_text(json.dumps(config))

        response = await async_client.get("/api/cron")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

        good = next(j for j in data["jobs"] if j["name"] == "good-job")
        assert good["error"] is None
        assert good["next_run"] is not None

        bad = next(j for j in data["jobs"] if j["name"] == "bad-job")
        assert bad["error"] == "Invalid schedule"
        assert bad["next_run"] is None

    async def test_no_cron_section_returns_empty(self, async_client: AsyncClient):
        """When config has no cron section, returns empty list."""
        response = await async_client.get("/api/cron")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["jobs"] == []

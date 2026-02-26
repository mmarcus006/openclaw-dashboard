"""Tests for GatewayService command history."""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


class TestGatewayHistory:
    """Tests for GET /api/gateway/history."""

    async def test_history_empty_initially(self, async_client: AsyncClient):
        """History is empty when no commands have been run."""
        response = await async_client.get("/api/gateway/history")
        assert response.status_code == 200
        data = response.json()
        assert data["commands"] == []
        assert data["total"] == 0

    async def test_history_records_command(self, async_client: AsyncClient):
        """After running a gateway command, history contains the entry."""
        with (
            patch("shutil.which", return_value="/usr/bin/openclaw"),
            patch(
                "app.services.gateway_service.GatewayService._run_cli",
                new_callable=AsyncMock,
                return_value=("Gateway started.", "", 0),
            ),
        ):
            await async_client.post("/api/gateway/start")

        response = await async_client.get("/api/gateway/history")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        entry = data["commands"][0]
        assert entry["command"] == "start"
        assert entry["exit_code"] == 0
        assert "timestamp" in entry

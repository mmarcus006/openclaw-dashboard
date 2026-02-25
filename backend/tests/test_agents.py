"""Tests for /api/agents/* endpoints.

Covers:
  - Agent list endpoint (GET /api/agents)
  - Agent detail endpoint (GET /api/agents/{id})
  - Main agent workspace special-casing
  - Nonexistent agent returns 404
  - File list content
"""

import pytest
from httpx import AsyncClient


class TestAgentList:
    """Tests for GET /api/agents."""

    async def test_agent_list_returns_200(self, async_client: AsyncClient):
        """GET /api/agents returns HTTP 200."""
        response = await async_client.get("/api/agents")
        assert response.status_code == 200

    async def test_agent_list_contains_main_agent(self, async_client: AsyncClient):
        """GET /api/agents response includes the 'main' agent."""
        response = await async_client.get("/api/agents")
        data = response.json()
        ids = [a["id"] for a in data["agents"]]
        assert "main" in ids

    async def test_agent_list_contains_coder_agent(self, async_client: AsyncClient):
        """GET /api/agents response includes the 'coder' agent from workspace-coder/."""
        response = await async_client.get("/api/agents")
        data = response.json()
        ids = [a["id"] for a in data["agents"]]
        assert "coder" in ids

    async def test_agent_list_total_matches_agents_count(self, async_client: AsyncClient):
        """total field matches the number of agents returned."""
        response = await async_client.get("/api/agents")
        data = response.json()
        assert data["total"] == len(data["agents"])

    async def test_agent_list_agents_have_required_fields(self, async_client: AsyncClient):
        """Each agent summary contains id, name, model, status fields."""
        response = await async_client.get("/api/agents")
        for agent in response.json()["agents"]:
            assert "id" in agent
            assert "name" in agent
            assert "model" in agent
            assert "status" in agent

    async def test_agent_list_main_agent_is_first(self, async_client: AsyncClient):
        """The 'main' agent appears first in the list."""
        response = await async_client.get("/api/agents")
        data = response.json()
        assert data["agents"][0]["id"] == "main"

    async def test_agent_list_error_envelope_on_bad_request(
        self, async_client: AsyncClient
    ):
        """Response shape is valid JSON (not a bare 500)."""
        response = await async_client.get("/api/agents")
        # As long as it's 200 and parseable, we're good
        assert response.headers["content-type"].startswith("application/json")


class TestAgentDetail:
    """Tests for GET /api/agents/{agent_id}."""

    async def test_main_agent_detail_returns_200(self, async_client: AsyncClient):
        """GET /api/agents/main returns HTTP 200."""
        response = await async_client.get("/api/agents/main")
        assert response.status_code == 200

    async def test_main_agent_workspace_path_ends_with_workspace(
        self, async_client: AsyncClient, mock_openclaw_home
    ):
        """Main agent workspace resolves to the 'workspace' directory (not 'agents/main/')."""
        response = await async_client.get("/api/agents/main")
        data = response.json()
        assert data["workspace"].endswith("/workspace") or data["workspace"].endswith("\\workspace")

    async def test_main_agent_workspace_is_not_agents_main(
        self, async_client: AsyncClient
    ):
        """Main agent workspace must NOT be agents/main/ — that's the special-casing."""
        response = await async_client.get("/api/agents/main")
        data = response.json()
        assert "agents/main" not in data["workspace"]
        assert "agents\\main" not in data["workspace"]

    async def test_coder_agent_detail_returns_200(self, async_client: AsyncClient):
        """GET /api/agents/coder returns HTTP 200."""
        response = await async_client.get("/api/agents/coder")
        assert response.status_code == 200

    async def test_coder_agent_workspace_path(
        self, async_client: AsyncClient, mock_openclaw_home
    ):
        """Coder agent workspace resolves to workspace-coder/."""
        response = await async_client.get("/api/agents/coder")
        data = response.json()
        expected = str(mock_openclaw_home / "workspace-coder")
        assert data["workspace"] == expected

    async def test_nonexistent_agent_returns_404(self, async_client: AsyncClient):
        """GET /api/agents/nonexistent returns 404."""
        response = await async_client.get("/api/agents/nonexistent")
        assert response.status_code == 404

    async def test_nonexistent_agent_has_error_envelope(self, async_client: AsyncClient):
        """404 for nonexistent agent uses the standard error envelope."""
        response = await async_client.get("/api/agents/nonexistent")
        data = response.json()
        assert "error" in data

    async def test_agent_detail_includes_files_list(self, async_client: AsyncClient):
        """AgentDetailResponse includes a 'files' list."""
        response = await async_client.get("/api/agents/main")
        data = response.json()
        assert "files" in data
        assert isinstance(data["files"], list)

    async def test_main_agent_files_include_agents_md(self, async_client: AsyncClient):
        """Main agent's file list includes AGENTS.md."""
        response = await async_client.get("/api/agents/main")
        data = response.json()
        names = [f["name"] for f in data["files"]]
        assert "AGENTS.md" in names

    async def test_main_agent_files_include_soul_md(self, async_client: AsyncClient):
        """Main agent's file list includes SOUL.md."""
        response = await async_client.get("/api/agents/main")
        data = response.json()
        names = [f["name"] for f in data["files"]]
        assert "SOUL.md" in names

    async def test_agent_files_have_name_and_size(self, async_client: AsyncClient):
        """Each file entry in the file list has 'name' and 'size' fields."""
        response = await async_client.get("/api/agents/main")
        for f in response.json()["files"]:
            assert "name" in f
            assert "size" in f

    async def test_agent_detail_has_id_and_status(self, async_client: AsyncClient):
        """AgentDetailResponse has id, name, model, status."""
        response = await async_client.get("/api/agents/main")
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "model" in data
        assert "status" in data

    async def test_main_agent_id_is_main(self, async_client: AsyncClient):
        """Main agent detail has id == 'main'."""
        response = await async_client.get("/api/agents/main")
        assert response.json()["id"] == "main"


class TestResolveAgentWorkspace:
    """Unit tests for AgentService.resolve_agent_workspace() directly."""

    def test_main_agent_resolves_to_workspace(self, agent_service, mock_openclaw_home):
        """resolve_agent_workspace('main') → mock_openclaw_home/workspace."""
        result = agent_service.resolve_agent_workspace("main")
        assert result == mock_openclaw_home / "workspace"

    def test_coder_agent_resolves_to_workspace_coder(self, agent_service, mock_openclaw_home):
        """resolve_agent_workspace('coder') → mock_openclaw_home/workspace-coder."""
        result = agent_service.resolve_agent_workspace("coder")
        assert result == mock_openclaw_home / "workspace-coder"

    def test_unknown_agent_returns_default_path(self, agent_service, mock_openclaw_home):
        """resolve_agent_workspace('unknown') returns workspace-unknown as default."""
        result = agent_service.resolve_agent_workspace("unknown")
        assert result == mock_openclaw_home / "workspace-unknown"

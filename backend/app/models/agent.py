from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AgentFileInfo(BaseModel):
    """Information about a file in an agent's workspace."""
    name: str = Field(..., description="File name")
    size: int = Field(..., description="File size in bytes")
    mtime: datetime = Field(..., description="Last modified timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "AGENTS.md",
                "size": 12400,
                "mtime": "2026-02-25T05:53:00Z"
            }
        }
    }


class AgentSummary(BaseModel):
    """Summary information about an agent."""
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent display name")
    model: str = Field(..., description="Model being used")
    status: str = Field(..., description="Agent status: active, idle, stopped")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "main",
                "name": "COS",
                "model": "anthropic/claude-opus-4-6",
                "status": "active",
                "last_activity": "2026-02-25T05:54:00Z"
            }
        }
    }


class AgentDetailResponse(BaseModel):
    """Detailed agent information including workspace files."""
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent display name")
    model: str = Field(..., description="Model being used")
    workspace: str = Field(..., description="Path to agent workspace")
    files: list[AgentFileInfo] = Field(default_factory=list, description="List of files in workspace")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    status: str = Field(..., description="Agent status: active, idle, stopped")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "main",
                "name": "COS",
                "model": "anthropic/claude-opus-4-6",
                "workspace": "/Users/miller/.openclaw/workspace",
                "files": [
                    {"name": "AGENTS.md", "size": 12400, "mtime": "2026-02-25T05:53:00Z"},
                    {"name": "SOUL.md", "size": 3800, "mtime": "2026-02-25T05:55:00Z"}
                ],
                "last_activity": "2026-02-25T05:54:00Z",
                "status": "active"
            }
        }
    }


class AgentListResponse(BaseModel):
    """Response containing list of all agents."""
    agents: list[AgentSummary] = Field(..., description="List of agent summaries")
    total: int = Field(..., description="Total number of agents")

    model_config = {
        "json_schema_extra": {
            "example": {
                "agents": [
                    {
                        "id": "main",
                        "name": "COS",
                        "model": "anthropic/claude-opus-4-6",
                        "status": "active",
                        "last_activity": "2026-02-25T05:54:00Z"
                    },
                    {
                        "id": "coder",
                        "name": "Coder",
                        "model": "anthropic/claude-sonnet-4-6",
                        "status": "idle",
                        "last_activity": "2026-02-25T04:30:00Z"
                    }
                ],
                "total": 2
            }
        }
    }

from datetime import datetime

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error information."""
    detail: dict | None = None


class ErrorResponse(BaseModel):
    """Standard error envelope for all error responses."""
    error: dict = Field(
        ...,
        description="Error object containing code, message, detail, and timestamp"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": {
                    "code": "FILE_NOT_FOUND",
                    "message": "File not found: SOUL.md",
                    "detail": {"agent_id": "coder", "path": "SOUL.md"},
                    "timestamp": "2026-02-25T06:00:00Z"
                }
            }
        }
    }


class FileContentResponse(BaseModel):
    """Response containing file content with metadata."""
    path: str = Field(..., description="File path relative to workspace")
    content: str = Field(..., description="File content")
    size: int = Field(..., description="File size in bytes")
    mtime: datetime = Field(..., description="Last modified timestamp")
    language: str = Field(..., description="Detected language for syntax highlighting")

    model_config = {
        "json_schema_extra": {
            "example": {
                "path": "AGENTS.md",
                "content": "# AGENTS.md - Your Workspace\n...",
                "size": 12400,
                "mtime": "2026-02-25T05:53:00Z",
                "language": "markdown"
            }
        }
    }


class SaveResponse(BaseModel):
    """Response after successful file save."""
    path: str = Field(..., description="File path that was saved")
    size: int = Field(..., description="New file size in bytes")
    mtime: datetime = Field(..., description="New modified timestamp")
    etag: str = Field(..., description="New ETag for the saved file")

    model_config = {
        "json_schema_extra": {
            "example": {
                "path": "AGENTS.md",
                "size": 12450,
                "mtime": "2026-02-25T06:00:00Z",
                "etag": "1708840800:12450"
            }
        }
    }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    openclaw_home: str = Field(..., description="Path to OpenClaw home directory")
    subsystems: dict = Field(..., description="Status of each subsystem")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok",
                "version": "1.0.0",
                "openclaw_home": "/Users/miller/.openclaw",
                "subsystems": {
                    "config": True,
                    "workspaces": True,
                    "gateway_cli": True,
                    "sessions": True
                }
            }
        }
    }

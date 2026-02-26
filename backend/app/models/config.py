from pydantic import BaseModel, Field
from typing import Optional


class ConfigResponse(BaseModel):
    """Response containing OpenClaw configuration (secrets redacted)."""
    config: dict = Field(..., description="OpenClaw configuration object")
    etag: str = Field(..., description="ETag for concurrency control")
    path: str = Field(..., description="Path to config file")

    model_config = {
        "json_schema_extra": {
            "example": {
                "config": {
                    "agents": {
                        "main": {
                            "model": "anthropic/claude-opus-4-6",
                            "workspace": "workspace"
                        }
                    },
                    "gateway": {
                        "port": 8400
                    }
                },
                "etag": "1708840800:2048",
                "path": "/Users/miller/.openclaw/openclaw.json"
            }
        }
    }


class ConfigValidateResponse(BaseModel):
    """Response from validating configuration."""
    valid: bool = Field(..., description="Whether the configuration is valid")
    errors: list[str] = Field(default_factory=list, description="List of validation errors")
    warnings: list[str] = Field(default_factory=list, description="List of validation warnings")

    model_config = {
        "json_schema_extra": {
            "example": {
                "valid": True,
                "errors": [],
                "warnings": ["Default workspace path may not exist"]
            }
        }
    }


class ConfigWriteRequest(BaseModel):
    """Request body for writing configuration."""
    config: dict = Field(..., description="Configuration object to save")
    etag: Optional[str] = Field(None, description="ETag for concurrency control")

    model_config = {
        "json_schema_extra": {
            "example": {
                "config": {
                    "agents": {
                        "main": {
                            "model": "anthropic/claude-opus-4-6"
                        }
                    }
                },
                "etag": "1708840800:2048"
            }
        }
    }

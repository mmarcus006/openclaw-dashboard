from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class GatewayAction(str, Enum):
    """Valid gateway actions - enum validated server-side."""
    START = "start"
    STOP = "stop"
    RESTART = "restart"


class GatewayStatusResponse(BaseModel):
    """Response containing gateway status information."""
    running: bool = Field(..., description="Whether the gateway is running")
    pid: Optional[int] = Field(None, description="Gateway process ID if running")
    uptime: Optional[str] = Field(None, description="Gateway uptime string")
    channels: dict = Field(default_factory=dict, description="Active channels")
    error: Optional[str] = Field(None, description="Error message if status unknown")

    model_config = {
        "json_schema_extra": {
            "example": {
                "running": True,
                "pid": 12345,
                "uptime": "2h 15m",
                "channels": {},
                "error": None
            }
        }
    }


class CommandResponse(BaseModel):
    """Response from a gateway command."""
    success: bool = Field(..., description="Whether the command succeeded")
    action: GatewayAction = Field(..., description="Action that was performed")
    message: str = Field(..., description="Human-readable response message")
    output: Optional[str] = Field(None, description="Command output if available")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "action": "restart",
                "message": "Gateway restarted successfully",
                "output": "Gateway stopped.\nGateway started."
            }
        }
    }


class GatewayCommandEntry(BaseModel):
    """A single gateway command execution record."""
    command: str = Field(..., description="Command that was run, e.g. 'start'")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    exit_code: int = Field(..., description="Process exit code (0 = success)")
    output: Optional[str] = Field(None, description="stdout/stderr snippet (max 500 chars)")


class GatewayHistoryResponse(BaseModel):
    """Response containing recent gateway command history."""
    commands: list[GatewayCommandEntry] = Field(default_factory=list)
    total: int = Field(..., description="Total number of stored commands")

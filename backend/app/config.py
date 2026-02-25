"""Application settings."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Dashboard configuration. All values can be overridden via environment variables."""

    OPENCLAW_HOME: Path = Path.home() / ".openclaw"
    HOST: str = "127.0.0.1"
    PORT: int = 8400
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]
    LOG_LEVEL: str = "INFO"

    @property
    def workspace(self) -> Path:
        return self.OPENCLAW_HOME / "workspace"

    @property
    def agents_dir(self) -> Path:
        return self.OPENCLAW_HOME / "agents"

    @property
    def config_path(self) -> Path:
        return self.OPENCLAW_HOME / "openclaw.json"

    @property
    def sessions_path(self) -> Path:
        return self.OPENCLAW_HOME / "sessions" / "sessions.json"

    model_config = {"env_prefix": "DASHBOARD_"}


settings = Settings()

"""FastAPI dependency injection providers.

All shared service instances are created once and injected via FastAPI's
Depends() mechanism.  Routes must never instantiate services directly.
"""

from functools import lru_cache

from app.config import Settings
from app.config import settings as _settings
from app.services.agent_service import AgentService
from app.services.config_service import ConfigService
from app.services.cron_service import CronService
from app.services.file_service import FileService
from app.services.gateway_service import GatewayService
from app.services.session_service import SessionService


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance.

    Returns:
        Application settings loaded from environment variables.
    """
    return _settings


@lru_cache(maxsize=1)
def get_file_service() -> FileService:
    """Return the singleton FileService instance.

    Returns:
        FileService configured with the current settings.
    """
    return FileService(settings=_settings)


@lru_cache(maxsize=1)
def get_agent_service() -> AgentService:
    """Return the singleton AgentService instance.

    Returns:
        AgentService that uses the shared FileService.
    """
    return AgentService(settings=_settings, file_service=get_file_service())


@lru_cache(maxsize=1)
def get_config_service() -> ConfigService:
    """Return the singleton ConfigService instance.

    Returns:
        ConfigService that manages openclaw.json read/write.
    """
    return ConfigService(settings=_settings, file_service=get_file_service())


@lru_cache(maxsize=1)
def get_gateway_service() -> GatewayService:
    """Return the singleton GatewayService instance.

    Returns:
        GatewayService wrapping the openclaw CLI subprocess.
    """
    return GatewayService(settings=_settings)


@lru_cache(maxsize=1)
def get_session_service() -> SessionService:
    """Return the singleton SessionService instance.

    Returns:
        SessionService that reads sessions.json and JSONL files.
    """
    return SessionService(settings=_settings)


@lru_cache(maxsize=1)
def get_cron_service() -> CronService:
    """Return the singleton CronService instance.

    Returns:
        CronService that reads cron jobs from openclaw.json.
    """
    return CronService(settings=_settings)

"""Cron job service — reads cron jobs from openclaw.json config."""

import json
from datetime import UTC, datetime

import structlog
from croniter import croniter

from app.config import Settings
from app.models.cron import CronJobEntry, CronJobListResponse

logger = structlog.get_logger(__name__)


class CronService:
    """Read and parse cron jobs from openclaw.json configuration."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def list_jobs(self) -> CronJobListResponse:
        """Read cron jobs from openclaw.json and return parsed list."""
        config_path = self._settings.config_path
        if not config_path.exists():
            return CronJobListResponse(jobs=[], total=0)

        try:
            raw = config_path.read_text(encoding="utf-8")
            config = json.loads(raw)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("cron_config_read_failed", error=str(exc))
            return CronJobListResponse(jobs=[], total=0)

        cron_jobs = config.get("cron", {})
        if not isinstance(cron_jobs, dict):
            return CronJobListResponse(jobs=[], total=0)

        jobs: list[CronJobEntry] = []
        now = datetime.now(UTC)

        for name, job_config in cron_jobs.items():
            if not isinstance(job_config, dict):
                continue

            schedule = job_config.get("schedule", "")
            enabled = job_config.get("enabled", True)
            schedule_human = schedule  # fallback

            next_run: str | None = None
            error: str | None = None

            try:
                cron = croniter(schedule, now)
                next_dt = cron.get_next(datetime)
                next_run = next_dt.isoformat()
            except (ValueError, KeyError, TypeError):
                error = "Invalid schedule"

            jobs.append(CronJobEntry(
                name=name,
                schedule=schedule,
                schedule_human=schedule_human,
                next_run=next_run,
                enabled=enabled,
                error=error,
            ))

        return CronJobListResponse(jobs=jobs, total=len(jobs))

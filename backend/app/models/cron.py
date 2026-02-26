"""Cron job models for the cron viewer."""

from pydantic import BaseModel, Field
from typing import Optional


class CronJobEntry(BaseModel):
    """A single cron job from openclaw.json config."""
    name: str = Field(..., description="Job name from config")
    schedule: str = Field(..., description="Raw cron expression")
    schedule_human: str = Field(..., description="Human-readable schedule")
    next_run: Optional[str] = Field(None, description="ISO 8601 next run time")
    enabled: bool = Field(..., description="Whether the job is enabled")
    error: Optional[str] = Field(None, description="Error message if schedule is invalid")


class CronJobListResponse(BaseModel):
    """Response containing cron job list."""
    jobs: list[CronJobEntry] = Field(default_factory=list)
    total: int = Field(..., description="Total number of cron jobs")

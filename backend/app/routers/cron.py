"""Cron router — /api/cron"""

from fastapi import APIRouter, Depends, status

from app.dependencies import get_cron_service
from app.models.cron import CronJobListResponse
from app.services.cron_service import CronService

router = APIRouter(prefix="/cron", tags=["cron"])


@router.get(
    "",
    response_model=CronJobListResponse,
    summary="List cron jobs",
    description="Read cron jobs from openclaw.json and return parsed list with next run times.",
    status_code=status.HTTP_200_OK,
)
async def list_cron_jobs(
    cron_svc: CronService = Depends(get_cron_service),
) -> CronJobListResponse:
    """Return cron jobs from config."""
    return cron_svc.list_jobs()

import logging
from datetime import UTC, datetime

from apscheduler.events import (  # type: ignore[import-untyped]
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED,
    JobExecutionEvent,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]

from md2blog.jobs.process_outbox import run as process_outbox
from md2blog.jobs.purge_expired_pages import purge_expired_pages

OUTBOX_PROCESS_INTERVAL_SECONDS = 5
TRASH_PURGE_HOUR_UTC = 19  # Asia/Seoul 04:00
logger = logging.getLogger(__name__)


def log_job_failure(event: JobExecutionEvent) -> None:
    if event.code == EVENT_JOB_MISSED:
        logger.warning(
            "scheduled job missed",
            extra={"event": "scheduler.job.missed", "job_id": event.job_id},
        )
        return

    error = event.exception
    logger.error(
        "scheduled job failed",
        extra={
            "event": "scheduler.job.failed",
            "job_id": event.job_id,
            "error_type": type(error).__name__ if error is not None else "UnknownError",
        },
    )


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=UTC)
    scheduler.add_listener(log_job_failure, EVENT_JOB_ERROR | EVENT_JOB_MISSED)
    startup_time = datetime.now(UTC)
    scheduler.add_job(
        process_outbox,
        trigger="interval",
        seconds=OUTBOX_PROCESS_INTERVAL_SECONDS,
        id="process-outbox",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=None,
        next_run_time=startup_time,
    )
    scheduler.add_job(
        purge_expired_pages,
        trigger="cron",
        hour=TRASH_PURGE_HOUR_UTC,
        minute=0,
        id="purge-expired-pages",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=None,
        next_run_time=startup_time,
    )
    return scheduler

from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]

from md2blog.jobs.process_outbox import run as process_outbox
from md2blog.jobs.purge_expired_pages import purge_expired_pages

OUTBOX_PROCESS_INTERVAL_SECONDS = 5
TRASH_PURGE_HOUR_UTC = 19  # Asia/Seoul 04:00


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=UTC)
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

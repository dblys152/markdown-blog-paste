from datetime import UTC

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from md2blog.jobs.scheduler import (
    OUTBOX_PROCESS_INTERVAL_SECONDS,
    TRASH_PURGE_HOUR_UTC,
    build_scheduler,
)


def test_scheduler_runs_recovery_jobs_immediately_and_then_on_schedule() -> None:
    scheduler = build_scheduler()
    jobs = {job.id: job for job in scheduler.get_jobs()}

    outbox_job = jobs["process-outbox"]
    assert isinstance(outbox_job.trigger, IntervalTrigger)
    assert outbox_job.trigger.interval.total_seconds() == OUTBOX_PROCESS_INTERVAL_SECONDS
    assert outbox_job.next_run_time.tzinfo == UTC
    assert outbox_job.max_instances == 1
    assert outbox_job.coalesce is True
    assert outbox_job.misfire_grace_time is None

    purge_job = jobs["purge-expired-pages"]
    assert isinstance(purge_job.trigger, CronTrigger)
    assert str(purge_job.trigger.fields[5]) == str(TRASH_PURGE_HOUR_UTC)
    assert purge_job.next_run_time.tzinfo == UTC
    assert purge_job.max_instances == 1
    assert purge_job.coalesce is True
    assert purge_job.misfire_grace_time is None

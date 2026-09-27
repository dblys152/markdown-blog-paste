from datetime import UTC, datetime
from unittest.mock import patch

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED, JobExecutionEvent
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from md2blog.jobs.scheduler import (
    OUTBOX_PROCESS_INTERVAL_SECONDS,
    TRASH_PURGE_HOUR_UTC,
    build_scheduler,
    log_job_failure,
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


def test_scheduler_logs_failed_job_without_exception_message() -> None:
    failure = JobExecutionEvent(
        EVENT_JOB_ERROR,
        "process-outbox",
        "default",
        datetime.now(UTC),
        exception=RuntimeError("sensitive database detail"),
    )

    with patch("md2blog.jobs.scheduler.logger.error") as log_error:
        log_job_failure(failure)

    assert log_error.call_args.args == ("scheduled job failed",)
    assert log_error.call_args.kwargs["extra"] == {
        "event": "scheduler.job.failed",
        "job_id": "process-outbox",
        "error_type": "RuntimeError",
    }


def test_scheduler_logs_missed_job() -> None:
    missed = JobExecutionEvent(
        EVENT_JOB_MISSED,
        "purge-expired-pages",
        "default",
        datetime.now(UTC),
    )

    with patch("md2blog.jobs.scheduler.logger.warning") as log_warning:
        log_job_failure(missed)

    assert log_warning.call_args.args == ("scheduled job missed",)
    assert log_warning.call_args.kwargs["extra"] == {
        "event": "scheduler.job.missed",
        "job_id": "purge-expired-pages",
    }

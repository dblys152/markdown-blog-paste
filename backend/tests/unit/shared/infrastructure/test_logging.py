import json
import logging

from md2blog.shared.infrastructure.logging import (
    JsonLogFormatter,
    bind_request_id,
    configure_logging,
    reset_request_id,
)


def test_json_log_formatter_includes_trace_and_whitelisted_fields() -> None:
    token = bind_request_id("trace-123")
    try:
        record = logging.LogRecord(
            name="md2blog.test",
            level=logging.WARNING,
            pathname=__file__,
            lineno=1,
            msg="outbox message failed",
            args=(),
            exc_info=None,
        )
        record.event = "outbox.message.failed"
        record.message_id = "10"
        record.payload = {"token": "secret"}

        payload = json.loads(JsonLogFormatter().format(record))
    finally:
        reset_request_id(token)

    assert payload["trace_id"] == "trace-123"
    assert payload["event"] == "outbox.message.failed"
    assert payload["message_id"] == "10"
    assert "payload" not in payload


def test_configure_logging_disables_duplicate_uvicorn_access_log() -> None:
    configure_logging("INFO")

    assert logging.getLogger("uvicorn.access").disabled is True


def test_configure_logging_suppresses_routine_apscheduler_logs() -> None:
    configure_logging("INFO")

    assert logging.getLogger("apscheduler").level == logging.WARNING

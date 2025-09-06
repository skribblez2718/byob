from __future__ import annotations

import logging
import structlog
from flask import g


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            timestamper,
            add_request_id,
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def add_request_id(logger, method_name, event_dict):
    req_id = getattr(g, "request_id", None)
    if req_id:
        event_dict["request_id"] = req_id
    return event_dict

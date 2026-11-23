"""
Structured logging with correlation IDs for distributed request tracing.

Provides structured JSON logging in production and readable formatting in development,
using the Python standard library logging module for zero external dependency overhead.
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variable for request correlation
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
request_meta_var: ContextVar[Dict[str, Any]] = ContextVar("request_meta", default={})


def get_correlation_id() -> str:
    """Get or generate a correlation ID for the current request."""
    cid = correlation_id_var.get()
    if cid is None:
        cid = str(uuid.uuid4())
        correlation_id_var.set(cid)
    return cid


def set_correlation_id(cid: str) -> None:
    """Set the correlation ID for the current request context."""
    correlation_id_var.set(cid)


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        cid = correlation_id_var.get()
        if cid:
            log_entry["correlation_id"] = cid

        meta = request_meta_var.get()
        if meta:
            log_entry["request"] = meta

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra kwargs passed to logger
        for key, val in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process"
            }:
                log_entry[key] = val

        return json.dumps(log_entry)


class ConsoleFormatter(logging.Formatter):
    """Readable colored formatting for local development."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        cid = correlation_id_var.get()
        cid_str = f" [{cid[:8]}]" if cid else ""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")

        msg = f"{color}{timestamp} [{record.levelname:>7}]{self.RESET}{cid_str} {record.name}: {record.getMessage()}"
        if record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"
        return msg


class StructuredLoggerAdapter:
    """Logger wrapper that formats key-value kwargs without parameter collisions."""

    FORBIDDEN_EXTRA_KEYS = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message"
    }

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _log(self, level: int, event: str, *args: Any, **kwargs: Any) -> None:
        if not self._logger.isEnabledFor(level):
            return

        standard_keys = {"exc_info", "stack_info", "stacklevel", "extra"}
        std_kwargs = {k: kwargs[k] for k in standard_keys if k in kwargs}
        custom_kwargs = {k: v for k, v in kwargs.items() if k not in standard_keys}

        if custom_kwargs:
            extra_str = " ".join(f"{k}={v}" for k, v in custom_kwargs.items())
            full_msg = f"{event} | {extra_str}"
        else:
            full_msg = event

        raw_extra = std_kwargs.get("extra", {})
        safe_extra = {}
        for k, v in {**raw_extra, **custom_kwargs}.items():
            safe_key = f"ctx_{k}" if k in self.FORBIDDEN_EXTRA_KEYS else k
            safe_extra[safe_key] = v

        std_kwargs["extra"] = safe_extra
        self._logger.log(level, full_msg, *args, **std_kwargs)

    def debug(self, event: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.DEBUG, event, *args, **kwargs)

    def info(self, event: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.INFO, event, *args, **kwargs)

    def warning(self, event: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.WARNING, event, *args, **kwargs)

    def error(self, event: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, event, *args, **kwargs)

    def critical(self, event: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, event, *args, **kwargs)

    def exception(self, event: str, *args: Any, **kwargs: Any) -> None:
        kwargs["exc_info"] = True
        self._log(logging.ERROR, event, *args, **kwargs)


def setup_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Configure logging handlers and formatters."""
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if json_logs:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(ConsoleFormatter())

    root.addHandler(handler)
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    for noisy in ("uvicorn.access", "httpcore", "httpx", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> StructuredLoggerAdapter:
    """Get a structured logger adapter."""
    logger = logging.getLogger(name)
    return StructuredLoggerAdapter(logger)

import json
import logging
import os

from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import has_request_context, request


SECURITY_LOGGER_NAME = "odiseopay.security"
DEFAULT_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"


def _log_dir() -> Path:
    return Path(os.getenv("SECURITY_LOG_DIR", DEFAULT_LOG_DIR))


def configure_security_logging() -> logging.Logger:
    """Crea el logger de seguridad con rotación de archivos."""
    logger = logging.getLogger(SECURITY_LOGGER_NAME)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    directory = _log_dir()
    directory.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        directory / "security.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    return logger


def _request_fields() -> dict:
    if not has_request_context():
        return {}

    fields = {
        "ip": request.remote_addr,
        "method": request.method,
        "path": request.path,
    }

    forwarded_for = request.headers.get("X-Forwarded-For")

    if forwarded_for:
        fields["forwarded_for"] = forwarded_for.split(",", 1)[0].strip()

    user_agent = request.headers.get("User-Agent")

    if user_agent:
        fields["user_agent"] = user_agent[:200]

    return fields


def log_security_event(event: str, outcome: str = "info", **fields) -> None:
    """Registra un evento de seguridad como una línea JSON."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": event,
        "outcome": outcome,
        **_request_fields(),
        **fields,
    }

    configure_security_logging().info(
        json.dumps(record, ensure_ascii=False, default=str)
    )

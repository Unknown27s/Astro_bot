"""
AstroBot Logging Module
Centralized logging setup with support for Sentry error tracking
"""

import logging
import logging.handlers
from pathlib import Path
from pythonjsonlogger import jsonlogger
from config import LOG_LEVEL, LOG_FILE_PATH, LOG_MAX_BYTES, LOG_BACKUP_COUNT


def setup_logging():
    """Configure logging with both file and console handlers, with JSON formatting."""

    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # Prevent duplicate handlers
    if root_logger.handlers:
        return root_logger

    # Create formatters
    json_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        timestamp=True
    )

    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler (rotating)
    log_file = Path(LOG_FILE_PATH)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    setup_logging()
    return logging.getLogger(name)

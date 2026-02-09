"""Logging configuration for ASUS Helper."""

import logging
import sys
from pathlib import Path

# Log file location
LOG_DIR = Path.home() / ".local" / "share" / "asus-helper"
LOG_FILE = LOG_DIR / "asus-helper.log"

# Create logger
logger = logging.getLogger("asus_helper")


def setup_logging(debug: bool = False) -> None:
    """Configure logging for the application.

    Args:
        debug: If True, set level to DEBUG and log to both file and console.
               If False, set level to INFO and log to file only.
    """
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatters
    detailed_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    simple_fmt = logging.Formatter("%(levelname)-8s | %(message)s")

    # File handler - always log everything
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_fmt)
        logger.addHandler(file_handler)
    except OSError as e:
        print(f"Warning: Could not create log file: {e}", file=sys.stderr)

    # Console handler - only in debug mode
    if debug:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(simple_fmt)
        logger.addHandler(console_handler)

    logger.debug("Logging initialized (debug=%s)", debug)
    logger.debug("Log file: %s", LOG_FILE)


def get_logger(name: str) -> logging.Logger:
    """Get a child logger with the given name.

    Args:
        name: Logger name (will be prefixed with 'asus_helper.')

    Returns:
        Logger instance.
    """
    return logging.getLogger(f"asus_helper.{name}")

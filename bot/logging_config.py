"""Logging configuration for the trading bot."""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime


def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """
    Configure application-wide logging.

    - DEBUG+ goes to a rotating log file (logs/trading_bot_YYYYMMDD.log)
    - WARNING+ goes to stderr (keeps the terminal clean)

    Returns the root 'trading_bot' logger.
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_path / f"trading_bot_{timestamp}.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if called more than once
    if root_logger.handlers:
        return logging.getLogger("trading_bot")

    # ── File handler ──────────────────────────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB per file
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # ── Console handler ───────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger = logging.getLogger("trading_bot")
    logger.info("Logging initialised — file: %s", log_file.resolve())
    return logger

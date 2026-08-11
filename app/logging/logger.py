import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config.settings import settings

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "project_audo.log"

logger = logging.getLogger("ProjectAudo")
logger.setLevel(logging.INFO)

# Attached directly to the named logger (not via logging.basicConfig()
# on the root logger) so this is deterministic under pytest, whose own
# logging plugin frequently pre-attaches a handler to the root logger -
# making basicConfig() a silent no-op there. logger.propagate stays at
# its default (True), so messages still reach the root logger too -
# this is what lets pytest's caplog fixture keep capturing them.
if not any(
    isinstance(handler, RotatingFileHandler)
    for handler in logger.handlers
):

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

"""
Covers Phase 3 of the live-paper-trading work: app/logging/logger.py's
switch from a plain FileHandler to a RotatingFileHandler, so a
weeks-long live process doesn't grow logs/project_audo.log unbounded.

Handlers are attached directly to the named "ProjectAudo" logger (not
via logging.basicConfig() on the root logger - see the module's
comment on why), so this test checks that logger's own handler list
rather than the root logger's, which pytest's own logging plugin
frequently pre-populates, making basicConfig() a no-op there.
"""

from logging.handlers import RotatingFileHandler

from app.config.settings import settings
from app.logging.logger import logger


def test_logger_uses_rotating_file_handler():

    rotating_handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler, RotatingFileHandler)
    ]

    assert len(rotating_handlers) == 1

    handler = rotating_handlers[0]

    assert handler.maxBytes == settings.log_max_bytes
    assert handler.backupCount == settings.log_backup_count

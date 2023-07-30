from app.logger import get_logger, set_log_level
from app.types import LogLevel
import logging


def test_get_logger():
    assert get_logger() == logging.getLogger(__name__)


def test_get_logger_with_name():
    assert get_logger("test") == logging.getLogger("test")


def test_set_log_level():
    set_log_level(LogLevel.WARNING)
    assert logging.getLogger().getEffectiveLevel() == logging.WARNING

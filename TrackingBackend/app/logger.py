from logging import StreamHandler
from .types import LogLevel
import logging
import inspect
import sys


def setup_logger() -> None:
    logger = logging.getLogger()
    # TODO: should probably load this from config or have it be set with a parameter
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(levelname)s || %(processName)s[%(process)d] --> %(name)s<[%(filename)s:%(lineno)d, %(funcName)s()]> :: %(message)s"
    )
    # Create the Handler for logging data to console
    console_handler = StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    # add handlers
    logger.addHandler(console_handler)


def set_log_level(level: LogLevel) -> None:
    logger = logging.getLogger()
    logger.setLevel(level.value)


def get_logger(name: str = "") -> logging.Logger:
    if name == "":
        # get calling module
        frm: inspect.FrameInfo = inspect.stack()[1]
        name = inspect.getmodule(frm[0]).__name__  # type: ignore

    logger = logging.getLogger(name)
    logger.debug("Initialized logger for %s", name)
    return logger

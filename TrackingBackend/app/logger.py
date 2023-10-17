from app.types import LogLevel
import logging
import inspect
import coloredlogs


def setup_logger() -> None:
    logger = logging.getLogger()
    # TODO: should probably load this from config or have it be set with a env var
    coloredlogs.install(
        level="DEBUG",
        logger=logger,
        fmt="%(levelname)s || %(processName)s[%(process)d] --> %(name)s<[%(filename)s:%(lineno)d],%(funcName)s()> :: %(message)s",
    )


def set_log_level(level: LogLevel) -> None:
    logger = logging.getLogger()
    logger.setLevel(level.value)


def get_logger(name: str = "") -> logging.Logger:
    if name == "":
        # get calling module
        frm: inspect.FrameInfo = inspect.stack()[1]
        name = inspect.getmodule(frm[0]).__name__  # type: ignore

    logger = logging.getLogger(name)
    return logger

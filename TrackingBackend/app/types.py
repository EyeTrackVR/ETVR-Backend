# This file exists purely because circular imports are a thing and im too lazy to come up with a better
# solution that doesnt involve a bunch of refactoring.
import os
import enum
import logging
from enum import Enum
from dataclasses import dataclass


# When we upgrade to python 3.11 we can use the built in StrEnum
class StrEnum(str, enum.Enum):
    def __new__(cls, value, *args, **kwargs):
        if not isinstance(value, (str, enum.auto)):
            raise TypeError(f"Values of StrEnums must be strings: {value!r} is a {type(value)}")
        return super().__new__(cls, value, *args, **kwargs)

    def __str__(self):
        return str(self.value)

    def _generate_next_value_(name, *_):
        return name


class Algorithms(StrEnum):
    HSF = "HSF"
    BLOB = "BLOB"
    LEAP = "LEAP"
    HSRAC = "HSRAC"
    RANSAC = "RANSAC"


class TrackerPosition(StrEnum):
    MOUTH = "mouth"
    LEFT_EYE = "left_eye"
    RIGHT_EYE = "right_eye"
    UNDEFINED = "undefined"


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class CameraState(Enum):
    DISCONNECTED = 0
    CONNECTED = 1
    CONNECTING = 2
    DISABLED = 3


@dataclass
class EyeData:
    x: float
    y: float
    blink: float
    position: TrackerPosition


DEBUG_FLAG = "ETVR_DEBUG"
TRACKING_FAILED = EyeData(0, 0, 0, TrackerPosition.UNDEFINED)
# This is a lambda because some modules are imported before the env variable is set / loaded
IS_DEBUG = lambda: os.environ.get(DEBUG_FLAG) not in [None, "0", "false", "False", "FALSE"]

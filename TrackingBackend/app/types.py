# This file exists purely because circular imports are a thing and im too lazy to come up with a better
# solution that doesnt involve a bunch of refactoring.
import logging
from enum import Enum
from dataclasses import dataclass


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class EyeID(Enum):
    LEFT = 0
    RIGHT = 1


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
    eye_id: EyeID

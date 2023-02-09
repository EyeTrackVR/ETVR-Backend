# This file exists purely because circular imports are a thing and im too lazy to come up with a better
# solution that doesnt involve a bunch of refactoring.
# If you have a better solution, please dont hesitate to shout at me in discord about my bad code, thanks!
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


@dataclass
class EyeData:
    x: int
    y: int
    blink: float
    eye_id: EyeID

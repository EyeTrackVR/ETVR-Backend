# This file exists purely because circular imports are a thing and im too lazy to come up with a better
# solution that doesnt involve a bunch of refactoring.
import logging
import numpy as np
from typing import Final
from enum import Enum, StrEnum
from dataclasses import dataclass


class Algorithms(StrEnum):
    HSF = "HSF"
    BLOB = "BLOB"
    LEAP = "LEAP"
    HSRAC = "HSRAC"
    RANSAC = "RANSAC"
    AHSF = "AHSF"


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


DEBUG_FLAG: Final = "ETVR_DEBUG"
EMPTY_FRAME: Final = np.zeros((1, 1), dtype=np.uint8)
TRACKING_FAILED: Final = EyeData(0, 0, 0, TrackerPosition.UNDEFINED)

from .logger import get_logger
from .camera import Camera
from .config import EyeTrackConfig
from enum import Enum
import queue
logger = get_logger()


class EyeID(Enum):
    LEFT = 0
    RIGHT = 1


class Tracker:
    def __init__(self, eye_id: EyeID, config: EyeTrackConfig):
        self.eye_id = eye_id
        self.config = config
        self.eye_config = (self.config.left_eye, self.config.right_eye)[bool(self.eye_id)]
        # Camera stuff
        self.image_queue: queue.Queue = queue.Queue()
        self.camera = Camera(self.eye_config, self.image_queue)

    def start(self) -> None:
        self.camera.start()

    def stop(self) -> None:
        self.camera.stop()

    def restart(self) -> None:
        self.camera.restart()

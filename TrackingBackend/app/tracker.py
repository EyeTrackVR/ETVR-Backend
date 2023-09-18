from __future__ import annotations
from .logger import get_logger
from .config import TrackerConfig
from app.processes import EyeProcessor, Camera
from multiprocessing.managers import SyncManager
from app.utils import clear_queue
from queue import Queue
from .types import EyeData
import cv2

logger = get_logger()

# TODO: when we start to integrate babble this should become a common interface that eye trackers and mouth trackers inherit from
class Tracker:
    def __init__(self, config: TrackerConfig, osc_queue: Queue[EyeData], manager: SyncManager):
        self.config = config
        self.uuid = config.uuid
        # IPC stuff
        self.manager = manager
        self.image_queue: Queue[cv2.Mat] = self.manager.Queue()
        # processes
        self.camera = Camera(self.config, self.image_queue)
        self.eye_processor = EyeProcessor(self.config, self.image_queue, osc_queue)

    def start(self) -> None:
        self.eye_processor.start()
        self.camera.start()

    def stop(self) -> None:
        self.camera.stop()
        self.eye_processor.stop()
        clear_queue(self.image_queue)

    def restart(self) -> None:
        self.camera.restart()
        self.eye_processor.restart()

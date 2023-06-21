from __future__ import annotations
import multiprocessing
import cv2
from multiprocessing import Queue
from .config import AlgorithmConfig
from .types import EyeID
from .logger import get_logger
import numpy as np

logger = get_logger()


class EyeProcessor:
    def __init__(self, image_queue: Queue[np.ndarray], config: AlgorithmConfig, eye_id: EyeID):
        self.image_queue: Queue = image_queue
        self.config: AlgorithmConfig = config
        self.eye_id: EyeID = eye_id
        # Threading stuff
        self.process: multiprocessing.Process = multiprocessing.Process()
        # setup all our algorithms, might be a good idea to use a map instead of multiple variables
        from app.algorithms import Blob, HSF, HSRAC, Ransac  # import here to avoid circular imports
        self.blob = Blob(self)
        self.hsf = HSF(self)
        self.hsrac = HSRAC(self)
        self.ransac = Ransac(self)
        

    def __del__(self):
        if self.process.is_alive():
            self.stop()

    def is_alive(self) -> bool:
        return self.process.is_alive()
    
    def start(self) -> None:
        # don't start a process if one already exists
        if self.process.is_alive():
            logger.debug(f"Process `{self.process.name}` requested to start but is already running")
            return

        logger.info(f"Starting `EyeProcessor {str(self.eye_id.name).capitalize()}`")
        # We need to recreate the process because it is not possible to start a process that has already been stopped
        self.process = multiprocessing.Process(target=self._run, name=f"EyeProcessor {str(self.eye_id.name).capitalize()}")
        self.process.start()

    def stop(self) -> None:
        # can't kill a non-existent process
        if not self.process.is_alive():
            logger.debug("Request to kill dead process was made!")
            return

        logger.info(f"Stopping process `{self.process.name}`")
        self.process.kill()

    def restart(self) -> None:
        self.stop()
        self.start()

    def _run(self) -> None:
        while True:
            try:
                current_frame = self.image_queue.get()
                cv2.imshow(f"{self.process.name}", current_frame)
                cv2.waitKey(1)
                # convert to grayscale, we don't need color
                current_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            except Exception:
                continue

            self.blob.run(current_frame)
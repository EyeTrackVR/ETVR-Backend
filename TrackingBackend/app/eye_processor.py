from __future__ import annotations
import multiprocessing
import cv2
from .config import AlgorithmConfig
from .types import EyeID, EyeData
from .logger import get_logger

logger = get_logger()


class EyeProcessor:
    def __init__(
        self,
        image_queue: multiprocessing.Queue[cv2.Mat],
        osc_queue: multiprocessing.Queue[EyeData],
        config: AlgorithmConfig,
        eye_id: EyeID,
    ):
        # Synced variables
        self.process: multiprocessing.Process = multiprocessing.Process()
        self.image_queue: multiprocessing.Queue[cv2.Mat] = image_queue
        self.osc_queue: multiprocessing.Queue[EyeData] = osc_queue
        # Unsynced variables
        self.config: AlgorithmConfig = config
        self.eye_id: EyeID = eye_id
        from app.algorithms import Blob, HSF, HSRAC, Ransac
        self.hsf: HSF = HSF(self)
        self.blob: Blob = Blob(self)
        self.hsrac: HSRAC = HSRAC(self)
        self.ransac: Ransac = Ransac(self)

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
        self.process.daemon = True
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
                # convert to grayscale, we don't need color
                current_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            except Exception:
                continue

            self.blob.run(current_frame)

            cv2.waitKey(1)

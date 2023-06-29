from __future__ import annotations
from .config import AlgorithmConfig
from app.utils import WorkerProcess
from .types import EyeID, EyeData
from queue import Queue
import cv2


class EyeProcessor(WorkerProcess):
    def __init__(
        self,
        image_queue: Queue[cv2.Mat],
        osc_queue: Queue[EyeData],
        config: AlgorithmConfig,
        eye_id: EyeID,
    ):
        super().__init__(name=f"Eye Processor {str(eye_id.name).capitalize()}")
        # Synced variables
        self.image_queue: Queue[cv2.Mat] = image_queue
        self.osc_queue = osc_queue
        # Unsynced variables
        self.config: AlgorithmConfig = config
        self.eye_id: EyeID = eye_id
        from app.algorithms import Blob, HSF, HSRAC, Ransac

        self.hsf: HSF = HSF(self)
        self.blob: Blob = Blob(self)
        self.hsrac: HSRAC = HSRAC(self)
        self.ransac: Ransac = Ransac(self)

    def __del__(self):
        super().__del__()

    def run(self) -> None:
        while True:
            try:
                current_frame = self.image_queue.get()
                cv2.imshow(f"{self.process_name()}", current_frame)
                # convert to grayscale, we don't need color
                current_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            except Exception:
                continue

            result = self.blob.run(current_frame, self.eye_id)
            self.osc_queue.put(result)

            cv2.waitKey(1)

from __future__ import annotations
from app.config import AlgorithmConfig, EyeTrackConfig
from app.utils import WorkerProcess, BaseAlgorithm
from app.types import EyeData, EyeID, Algorithms
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
        self.algorithms: list[BaseAlgorithm] = []
        self.config: AlgorithmConfig = config
        self.eye_id: EyeID = eye_id
        # fmt: off
        from app.algorithms import Blob, HSF, HSRAC, Ransac
        self.hsf: HSF = HSF(self)
        self.blob: Blob = Blob(self)
        self.hsrac: HSRAC = HSRAC(self)
        self.ransac: Ransac = Ransac(self)
        # fmt: on

    def startup(self) -> None:
        self.setup_algorithms()

    def run(self) -> None:
        try:
            current_frame = self.image_queue.get(block=True, timeout=0.5)
            cv2.imshow(f"{self.process_name()}", current_frame)
            current_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        except Exception:
            return

        result = EyeData(0, 0, 0, self.eye_id)
        for algorithm in self.algorithms:
            result = algorithm.run(current_frame, self.eye_id)

        self.osc_queue.put(result)
        cv2.waitKey(1)

    def shutdown(self) -> None:
        pass

    def on_config_update(self, config: EyeTrackConfig) -> None:
        self.config = config.algorithm
        self.setup_algorithms()

    def setup_algorithms(self) -> None:
        self.algorithms.clear()
        for algorithm in self.config.algorithm_order:
            if algorithm == Algorithms.BLOB:
                self.algorithms.append(self.blob)
            elif algorithm == Algorithms.HSF:
                self.algorithms.append(self.hsf)
            elif algorithm == Algorithms.HSRAC:
                self.algorithms.append(self.hsrac)
            elif algorithm == Algorithms.RANSAC:
                self.algorithms.append(self.ransac)
            else:
                self.logger.warning(f"Unknown algorithm {algorithm}")

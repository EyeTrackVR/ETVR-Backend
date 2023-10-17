from app.types import EyeData, Algorithms, TRACKING_FAILED
from app.config import AlgorithmConfig, TrackerConfig
from app.utils import WorkerProcess, BaseAlgorithm
from cv2.typing import MatLike
from queue import Queue
import cv2


class EyeProcessor(WorkerProcess):
    def __init__(
        self,
        tracker_config: TrackerConfig,
        image_queue: Queue[MatLike],
        osc_queue: Queue[EyeData],
    ):
        super().__init__(name=f"Eye Processor {str(tracker_config.name)}", uuid=tracker_config.uuid)
        # Synced variables
        self.image_queue = image_queue
        self.osc_queue = osc_queue
        # Unsynced variables
        self.algorithms: list[BaseAlgorithm] = []
        self.config: AlgorithmConfig = tracker_config.algorithm
        self.tracker_position = tracker_config.tracker_position

    def startup(self) -> None:
        self.setup_algorithms()

    def run(self) -> None:
        try:
            current_frame = self.image_queue.get(block=True, timeout=0.5)
            self.window.imshow(f"{self.process_name()}", current_frame)
            current_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        except Exception:
            return

        result = EyeData(0, 0, 0, self.tracker_position)
        for algorithm in self.algorithms:
            result = algorithm.run(current_frame)

            if result == TRACKING_FAILED:
                self.logger.debug(f"Algorithm {algorithm.__class__.__name__} failed to find a result")
                continue
            break

        self.osc_queue.put(result)
        self.window.imshow(f"{self.process_name()}, output", current_frame)

    def shutdown(self) -> None:
        pass

    def on_tracker_config_update(self, tracker_config: TrackerConfig) -> None:
        self.config = tracker_config.algorithm
        self.tracker_position = tracker_config.tracker_position
        self.setup_algorithms()

    def setup_algorithms(self) -> None:
        from app.algorithms import Blob, HSF, HSRAC, Ransac, Leap

        self.algorithms.clear()
        for algorithm in self.config.algorithm_order:
            match algorithm:
                case Algorithms.BLOB:
                    self.algorithms.append(Blob(self))
                case Algorithms.HSF:
                    self.algorithms.append(HSF(self))
                case Algorithms.HSRAC:
                    self.algorithms.append(HSRAC(self))
                case Algorithms.RANSAC:
                    self.algorithms.append(Ransac(self))
                case Algorithms.LEAP:
                    self.algorithms.append(Leap(self))
                case _:
                    self.logger.warning(f"Unknown algorithm: {algorithm}")

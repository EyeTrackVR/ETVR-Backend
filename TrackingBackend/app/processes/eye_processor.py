from app.types import EyeData, Algorithms, TRACKING_FAILED
from app.config import AlgorithmConfig, TrackerConfig
from app.utils import WorkerProcess, BaseAlgorithm
from cv2.typing import MatLike
from queue import Queue, Full
import queue
import cv2


class EyeProcessor(WorkerProcess):
    def __init__(
        self,
        tracker_config: TrackerConfig,
        image_queue: Queue[MatLike],
        osc_queue: Queue[EyeData],
        frontend_queue: Queue[MatLike],
    ):
        super().__init__(name=f"Eye Processor {str(tracker_config.name)}", uuid=tracker_config.uuid)
        # Synced variables
        self.frontend_queue = frontend_queue
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
            current_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        except queue.Empty:
            return
        except Exception:
            self.logger.exception("Failed to get image from queue")
            return

        # TODO: if we need to run more than 1 algorithm, each should receive a clean frame and return a frame with visualizations + the eye data
        # We could keep an array of visualizations and then merge them all at the end for presentation
        result = EyeData(0, 0, 0, self.tracker_position)
        for algorithm in self.algorithms:
            result = algorithm.run(current_frame, self.tracker_position)

            if result == TRACKING_FAILED:
                self.logger.debug(f"Algorithm {algorithm.get_name()} failed to find a result")
                continue
            break

        try:
            self.osc_queue.put(result)
            self.frontend_queue.put(current_frame, block=False)
        except Full:
            pass
        self.window.imshow(self.process_name(), current_frame)

    def shutdown(self) -> None:
        pass

    def on_tracker_config_update(self, tracker_config: TrackerConfig) -> None:
        self.config = tracker_config.algorithm
        self.tracker_position = tracker_config.tracker_position
        self.setup_algorithms()

    def setup_algorithms(self) -> None:
        from app.algorithms import Blob, HSF, HSRAC, Leap, AHSF

        self.algorithms.clear()
        for algorithm in self.config.algorithm_order:
            match algorithm:
                case Algorithms.BLOB:
                    self.algorithms.append(Blob(self))
                case Algorithms.HSF:
                    self.algorithms.append(HSF(self))
                case Algorithms.HSRAC:
                    self.algorithms.append(HSRAC(self))
                # case Algorithms.RANSAC:
                #     self.algorithms.append(RANSAC(self))
                case Algorithms.LEAP:
                    self.algorithms.append(Leap(self))
                case Algorithms.AHSF:
                    self.algorithms.append(AHSF(self))
                case _:
                    self.logger.warning(f"Unknown algorithm: {algorithm}")

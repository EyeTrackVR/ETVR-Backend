from queue import Queue, Empty, Full
import numpy as np

from ..types import EyeData, TRACKING_FAILED
from ..utils import WorkerProcess
from ..calibration import CalibrationEllipse


class CalibrationProcessor(WorkerProcess):
    def __init__(
        self,
        input_queue: Queue[EyeData],
        output_queue: Queue[EyeData],
        state,
        name: str,
        uuid: str,
    ):
        super().__init__(name=f"Calibration {name}", uuid=uuid)
        # Synced variables
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.state = state
        # Unsynced variables
        self.calibration = CalibrationEllipse()
        self.recenter_reference: np.ndarray | None = None
        self._prev_calibrating = False

    def startup(self) -> None:
        pass

    def run(self) -> None:
        try:
            eye_data: EyeData = self.input_queue.get(block=True, timeout=0.5)
        except Empty:
            return
        except Exception:
            self.logger.exception("Failed to get eye data from queue")
            return

        calibrating = bool(self.state.get("calibrating", False))
        if calibrating and not self._prev_calibrating:
            self.calibration = CalibrationEllipse()
            self.state["calibrated"] = False
            self.state["samples"] = 0

        if not calibrating and self._prev_calibrating:
            self.calibration.fit_ellipse()
            self.state["calibrated"] = bool(self.calibration.fitted)
            self.state["samples"] = len(self.calibration.xs)

        self._prev_calibrating = calibrating

        if self.state.get("recenter_requested", False):
            self.recenter_reference = np.array([eye_data.x, eye_data.y], dtype=float)
            self.state["recenter_requested"] = False
            self.state["recentered"] = True

        if calibrating and eye_data != TRACKING_FAILED:
            self.calibration.add_sample(eye_data.x, eye_data.y)
            self.state["samples"] = len(self.calibration.xs)

        if self.calibration.fitted:
            norm_x, norm_y = self.calibration.normalize((eye_data.x, eye_data.y), target_pos=self.recenter_reference)
            eye_data.x = (norm_x + 1.0) / 2.0
            eye_data.y = (norm_y + 1.0) / 2.0

        try:
            self.output_queue.put(eye_data, block=False)
        except Full:
            pass

    def shutdown(self) -> None:
        pass

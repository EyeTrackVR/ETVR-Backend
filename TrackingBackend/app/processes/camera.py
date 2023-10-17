from app.config import CameraConfig, TrackerConfig
from app.utils import WorkerProcess
from app.types import CameraState
from multiprocessing import Value
from cv2.typing import MatLike
from queue import Queue
import ctypes
import cv2

# fmt: off
OPENCV_PARAMS = [
    cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2500,
    cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2500,
]
BACKEND = cv2.CAP_FFMPEG
# fmt: on


class Camera(WorkerProcess):
    def __init__(self, tracker_config: TrackerConfig, image_queue: Queue[MatLike]):
        super().__init__(name=f"Capture {str(tracker_config.name)}", uuid=tracker_config.uuid)
        # Synced variables
        self.image_queue = image_queue
        self.state = Value(ctypes.c_int, CameraState.DISCONNECTED.value)
        # Unsynced variables
        self.config: CameraConfig = tracker_config.camera
        self.current_capture_source: str = self.config.capture_source
        self.camera: cv2.VideoCapture = None  # type: ignore[assignment]

    def startup(self) -> None:
        if self.camera is None:
            self.camera = cv2.VideoCapture()

        if self.config.capture_source == "" or self.current_capture_source == "":
            self.logger.info("No capture source set, waiting for config update")

    def run(self) -> None:
        if self.config.capture_source != "":
            # if the camera is disconnected or the capture source has changed, reconnect
            if self.get_state() == CameraState.DISCONNECTED or self.current_capture_source != self.config.capture_source:
                self.connect_camera()
            else:
                self.get_camera_image()
        else:
            self.set_state(CameraState.DISCONNECTED)

    def shutdown(self) -> None:
        if self.camera.isOpened():
            self.camera.release()

    def on_tracker_config_update(self, tracker_config: TrackerConfig) -> None:
        self.config = tracker_config.camera

    def connect_camera(self) -> None:
        self.set_state(CameraState.CONNECTING)
        self.current_capture_source = self.config.capture_source
        self.logger.info(f"Connecting to capture source {self.current_capture_source}")
        try:
            self.camera.setExceptionMode(True)
            # https://github.com/opencv/opencv/issues/23207
            self.camera.open(self.current_capture_source, BACKEND, OPENCV_PARAMS)
            if self.camera.isOpened():
                self.set_state(CameraState.CONNECTED)
                self.logger.info(f"Camera connected with backend: {self.camera.getBackendName()}")
            else:
                raise cv2.error
        except (cv2.error, Exception):
            self.set_state(CameraState.DISCONNECTED)
            self.logger.info(f"Capture source {self.current_capture_source} not found, retrying")

    def get_camera_image(self) -> None:
        try:
            ret, frame = self.camera.read()
            if not ret:
                self.camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.logger.warning("Capture source problem, assuming camera disconnected, waiting for reconnect.")
                self.set_state(CameraState.DISCONNECTED)
                return
            frame_number: float = self.camera.get(cv2.CAP_PROP_POS_FRAMES)
            fps: float = self.camera.get(cv2.CAP_PROP_FPS)
            self.push_image_to_queue(frame, frame_number, fps)
        except (cv2.error, Exception):
            self.set_state(CameraState.DISCONNECTED)
            self.logger.warning("Failed to retrieve or push frame to queue, Assuming camera disconnected, waiting for reconnect.")

    def push_image_to_queue(self, frame: MatLike, frame_number: float, fps: float) -> None:
        try:
            if self.config.flip_x_axis:
                frame = cv2.flip(frame, 0)

            if self.config.flip_y_axis:
                frame = cv2.flip(frame, 1)

            qsize: int = self.image_queue.qsize()
            if qsize > 50:
                self.logger.warning(f"CAPTURE QUEUE BACKPRESSURE OF {qsize}. CHECK FOR CRASH OR TIMING ISSUES IN ALGORITHM.")
                pass
            self.image_queue.put(frame)
        except Exception:
            self.logger.exception("Failed to push to camera capture queue!")

    def get_state(self) -> CameraState:
        return CameraState(self.state.get_obj().value)

    def set_state(self, state: CameraState) -> None:
        # since we cant sync enums directly, so we sync the value of the enum instead
        self.state.get_obj().value = state.value

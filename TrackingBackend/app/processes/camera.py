from app.utils import WorkerProcess, mat_crop, mat_rotate, clear_queue, is_serial
from app.config import CameraConfig, TrackerConfig
from app.types import CameraState
from multiprocessing import Value
import serial.tools.list_ports
from cv2.typing import MatLike
from typing import Final
from queue import Queue
import numpy as np
import ctypes
import serial
import time
import cv2
import os

# fmt: off
OPENCV_PARAMS: Final = [
    cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2500,
    cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2500,
]
OPENCV_BACKEND: Final = cv2.CAP_FFMPEG
QUEUE_BACKPRESSURE_THRESHOLD: Final = 50

"""
header-begin (2 bytes)
header-type (2 bytes)
packet-size (2 bytes)
packet (packet-size bytes)
"""
ETVR_HEADER_LENGTH: Final = 6
ETVR_HEADER: Final = b"\xff\xa0"
ETVR_HEADER_NAME: Final = b"\xff\xa1"
COM_PORT_NOT_FOUND_TIMEOUT: Final = 2.5
# fmt: on


class Camera(WorkerProcess):
    def __init__(self, tracker_config: TrackerConfig, image_queue: Queue[MatLike], frontend_queue: Queue[MatLike]):
        super().__init__(name=f"Capture {str(tracker_config.name)}", uuid=tracker_config.uuid)
        # Synced variables
        self.image_queue = image_queue
        self.frontend_queue = frontend_queue
        self.state = Value(ctypes.c_int, CameraState.DISCONNECTED.value)
        # Unsynced variables
        self.serial_frame_number: int = 0  # if we ever get a bug report where this overflows I will cry
        self.config: CameraConfig = tracker_config.camera
        self.current_capture_source: str = self.config.capture_source
        # these objects are None by default, because they arent picklable
        self.camera: cv2.VideoCapture = None  # type: ignore[assignment]
        self.serial_camera: serial.Serial = None  # type: ignore[assignment]

    def startup(self) -> None:
        if self.camera is None:
            self.camera = cv2.VideoCapture()
        if self.serial_camera is None:
            self.serial_camera = serial.Serial()

        if self.config.capture_source == "" or self.current_capture_source == "":
            self.logger.info("No capture source set, waiting for config update")

    def run(self) -> None:
        if self.config.capture_source == "":
            self.set_state(CameraState.DISCONNECTED)
            return

        # if the camera is disconnected or the capture source has changed, reconnect
        if self.get_state() == CameraState.DISCONNECTED or self.current_capture_source != self.config.capture_source:
            self.set_state(CameraState.CONNECTING)
            self.current_capture_source = self.config.capture_source
            if is_serial(self.current_capture_source):
                self.connect_serial_camera()
            else:
                self.connect_camera()
        else:
            if is_serial(self.current_capture_source):
                self.get_serial_image()
            else:
                self.get_camera_image()

    def shutdown(self) -> None:
        if self.camera.isOpened() and self.camera is not None:
            self.camera.release()

        if self.serial_camera.is_open and self.serial_camera is not None:
            self.serial_camera.close()

    def on_tracker_config_update(self, tracker_config: TrackerConfig) -> None:
        self.config = tracker_config.camera

    # region: OpenCV camera implementation
    def connect_camera(self) -> None:
        self.logger.info(f"Connecting to capture source {self.current_capture_source}")
        try:
            self.camera.setExceptionMode(True)
            # https://github.com/opencv/opencv/issues/23207
            self.camera.open(self.current_capture_source, OPENCV_BACKEND, OPENCV_PARAMS)
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
                self.logger.warning("Capture source problem, assuming camera disconnected, waiting for reconnect.")
                self.camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.set_state(CameraState.DISCONNECTED)
                return
            frame_number: float = self.camera.get(cv2.CAP_PROP_POS_FRAMES)
            fps: float = self.camera.get(cv2.CAP_PROP_FPS)
            self.push_image_to_queue(frame, frame_number, fps)
        except (cv2.error, Exception):
            self.set_state(CameraState.DISCONNECTED)
            self.logger.warning("Failed to retrieve or push frame to queue, Assuming camera disconnected, waiting for reconnect.")

    # endregion

    # region: Serial camera implementation
    def connect_serial_camera(self) -> None:
        self.logger.info(f"Connecting to serial capture source {self.current_capture_source}")
        if not any(p for p in serial.tools.list_ports.comports() if self.config.capture_source in p):
            self.logger.warning(f"Serial port `{self.current_capture_source}` not found, waiting for reconnect.")
            self.set_state(CameraState.DISCONNECTED)
            time.sleep(COM_PORT_NOT_FOUND_TIMEOUT)
            return

        try:
            self.serial_camera = serial.Serial(
                port=self.current_capture_source, baudrate=3000000, xonxoff=False, dsrdtr=False, rtscts=False
            )
            # The `set_buffer_size` method is only available on Windows
            if os.name == "nt":
                self.serial_camera.set_buffer_size(rx_size=32768, tx_size=32768)
            self.logger.info(f"Serial camera connected to `{self.current_capture_source}`")
            self.set_state(CameraState.CONNECTED)
        except Exception:
            self.logger.exception(f"Failed to connect to serial port `{self.current_capture_source}`")
            self.set_state(CameraState.DISCONNECTED)

    # TODO: maybe move this into `get_serial_image`?
    def serial_fetch_frame(self) -> bytes:
        buffer = b""
        while True:
            buffer += self.serial_camera.read(2048)
            beg = buffer.find(ETVR_HEADER + ETVR_HEADER_NAME)
            if beg != -1:
                break

        # discard any data before header
        if beg > 0:
            buffer = buffer[beg:]
            beg = 0
        end = int.from_bytes(buffer[4:6], byteorder="little")
        buffer += self.serial_camera.read(end - len(buffer))

        frame = buffer[beg + ETVR_HEADER_LENGTH : end + ETVR_HEADER_LENGTH]
        buffer = buffer[end + ETVR_HEADER_LENGTH :]

        # drop any potentially outdated frames
        if self.serial_camera.in_waiting > 32768:
            self.logger.warning(f"Discarding serial buffer ({self.serial_camera.in_waiting} bytes)")
            self.serial_camera.reset_input_buffer()

        return frame

    def get_serial_image(self) -> None:
        if self.serial_camera is None or not self.serial_camera.is_open:
            self.logger.warning("Serial camera disconnected, waiting for reconnect.")
            self.set_state(CameraState.DISCONNECTED)
            return

        try:
            if self.serial_camera.in_waiting:
                image = self.serial_fetch_frame()
                frame = cv2.imdecode(np.frombuffer(image, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
                if frame is None:
                    self.logger.warning("Failed to decode serial camera frame, discarding")
                    return

                self.serial_frame_number += 1
                fps = round(1.0 / self.delta_time)
                self.push_image_to_queue(frame, self.serial_frame_number, fps)
        except Exception:
            self.logger.exception("Serial capture error, assuming disconnect, waiting for reconnect.")
            self.set_state(CameraState.DISCONNECTED)
            self.serial_camera.close()

    # endregion

    def preprocess_frame(self, frame: MatLike) -> MatLike:
        # flip the frame if needed
        if self.config.flip_x_axis:
            frame = cv2.flip(frame, 0)
        if self.config.flip_y_axis:
            frame = cv2.flip(frame, 1)

        frame = mat_rotate(frame, self.config.rotation)
        # send frame to frontend
        self.frontend_queue.put(frame)
        frame = mat_crop(self.config.roi_x, self.config.roi_y, self.config.roi_w, self.config.roi_h, frame)

        return frame

    def push_image_to_queue(self, frame: MatLike, frame_number: float, fps: float) -> None:
        try:
            self.window.imshow(self.process_name(), frame)
            frame = self.preprocess_frame(frame)
            qsize: int = self.image_queue.qsize()
            if qsize > QUEUE_BACKPRESSURE_THRESHOLD:
                self.logger.warning(f"Capture queue backpressure of {qsize}, dropping frames...")
                clear_queue(self.image_queue)

            self.image_queue.put(frame)
            # self.image_queue.put(frame, frame_number, fps)
        except Exception:
            self.logger.exception("Failed to push to camera capture queue!")

    def get_state(self) -> CameraState:
        return CameraState(self.state.get_obj().value)

    def set_state(self, state: CameraState) -> None:
        # since we cant sync enums directly, so we sync the value of the enum instead
        self.state.get_obj().value = state.value

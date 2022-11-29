from .logger import get_logger
from .config import CameraConfig
import cv2
import queue
import threading
from enum import Enum
logger = get_logger()


class CameraState(Enum):
    DISCONNECTED = 0
    CONNECTED = 1
    CONNECTING = 2


class Camera:
    def __init__(self, config: CameraConfig, out_queue: queue.Queue, cancellation_event: threading.Event):
        self.config = config
        self.cancellation_event = cancellation_event
        self.camera_state = CameraState.DISCONNECTED
        self.current_capture_source = self.config.capture_source
        self.out_queue = out_queue
        self.camera: cv2.VideoCapture = None

    def run(self) -> None:
        while True:
            if self.cancellation_event.is_set():
                logger.info("Exiting capture thread")
                return
            # If things aren't open, retry until they are. Don't let read requests come in any earlier
            # than this, otherwise we can deadlock ourselves.
            if self.config.capture_source != "":
                if self.camera_state == CameraState.DISCONNECTED or self.current_capture_source != self.config.capture_source:
                    self.connect_camera()
                else:
                    # TODO: if log is full of warning just add the capture event back and check it before this function
                    self.get_camera_image()
            else:  # no capture source is defined yet, so we wait :3
                self.camera_state = CameraState.DISCONNECTED

    def connect_camera(self) -> None:
        try:
            self.camera_state = CameraState.CONNECTING
            self.current_capture_source = self.config.capture_source
            # try open the camera
            self.camera = cv2.VideoCapture(self.current_capture_source)
            # check if we opened it
            if self.camera.isOpened():
                self.camera_state = CameraState.CONNECTED
                logger.info("Camera connected!")
                return
            self.camera_state = CameraState.DISCONNECTED
            logger.info(f"Capture source {self.current_capture_source} not found, retrying")
        except cv2.error:
            logger.exception("Something is very broken")

    def get_camera_image(self) -> None:
        try:
            ret, image = self.camera.read()
            if not ret:
                self.camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
                logger.error("Problem getting frame")
                return
            frame_number = self.camera.get(cv2.CAP_PROP_POS_FRAMES)
            fps = self.camera.get(cv2.CAP_PROP_FPS)
            self.push_image_to_queue(image, frame_number, fps)
        except (cv2.error, Exception):
            logger.warning("Capture source problem, assuming camera disconnected, waiting for reconnect.")
            self.camera_state = CameraState.DISCONNECTED

    def push_image_to_queue(self, image, frame_number, fps) -> None:
        # If there's backpressure, just yell. We really shouldn't have this unless we start getting
        # some sort of capture event conflict though.
        qsize = self.out_queue.qsize()
        if qsize > 1:
            logger.warning(f"CAPTURE QUEUE BACKPRESSURE OF {qsize}. CHECK FOR CRASH OR TIMING ISSUES IN ALGORITHM.")
        self.out_queue.put(image, frame_number, fps)

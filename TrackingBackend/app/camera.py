from __future__ import annotations
from .logger import get_logger
from .config import CameraConfig
from .types import CameraState, EyeID
import multiprocessing
import cv2
import os

# may or may not be needed, but it's here just in case
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout;1000"
logger = get_logger()

# FIXME:
#----------------------------------------------------------------------------------------------------------------------------
# currently the only problem here is that we arent sharing memory between processes
# when starting the camera process, it creates a copy off all the variables in the current process, including class members
# this means that when we change the config in the main process, the camera process doesn't see the changes
# and if we change camera_state in the camera process, the main process doesn't see the changes either
# luckily most of the important data (osc stuff, camera data, eye position, etc...) can be shared using a multiprocessing.Queue, 
# so we don't need to worry about that because the multiprocessing.Queue object is shared between processes
# however, we do need to worry about the config and class variables as they are not using a Queue and are not shared
# one solution would be to use a shared memory object, but that would require a lot of refactoring
# another solution would be to use a manager object, but that would also require a decent amount of refactoring
# the easiest solution would be to just use multiprocessing.Value and multiprocessing.Array objects
# this problem also exists to some degree in osc.py and eye_tracker.py
#----------------------------------------------------------------------------------------------------------------------------

class Camera:
    def __init__(self, config: CameraConfig, eye_id: EyeID, image_queue: multiprocessing.Queue[cv2.Mat]):
        self.eye_id: EyeID = eye_id
        self.config: CameraConfig = config
        self.camera_state = CameraState.DISCONNECTED
        self.current_capture_source: str = self.config.capture_source
        self.process: multiprocessing.Process = multiprocessing.Process()
        # we are using None as a placeholder for the camera object because we can't create it until we are in the process
        # otherwise we make multiprocessing sad :(
        self.camera: cv2.VideoCapture = None
        self.image_queue: multiprocessing.Queue[cv2.Mat] = image_queue
        logger.debug("Initialized Camera object")

    def __del__(self):
        if self.process.is_alive():
            self.stop()

    def is_alive(self) -> bool:
        return self.process.is_alive()

    def get_status(self) -> CameraState:
        return self.camera_state

    def start(self) -> None:
        # don't start a process if one already exists
        if self.process.is_alive():
            logger.debug(f"Process `{self.process.name}` requested to start but is already running")
            return

        logger.info(f"Starting `Capture {str(self.eye_id.name).capitalize()}`")
        # We need to recreate the process because it is not possible to start a process that has already been stopped
        self.process = multiprocessing.Process(target=self._run, name=f"Capture {str(self.eye_id.name).capitalize()}")
        self.process.start()

    def stop(self) -> None:
        # can't kill a non-existent process
        if not self.process.is_alive():
            logger.debug("Request to kill dead process thread was made!")
            return

        logger.info(f"Stopping process `{self.process.name}`")
        self.process.kill()

    def restart(self) -> None:
        self.stop()
        self.start()

    def _run(self) -> None:
        self.camera = cv2.VideoCapture()
        while True:
            # If things aren't open, retry until they are. Don't let read requests come in any earlier than this,
            # otherwise we can deadlock ourselves.
            if self.config.capture_source != "":
                # if the camera is disconnected or the capture source has changed, reconnect
                if self.camera_state == CameraState.DISCONNECTED or self.current_capture_source != self.config.capture_source:
                    self.connect_camera()
                else:
                    self.get_camera_image()
            else:  # no capture source is defined yet, so we wait :3
                self.camera_state = CameraState.DISCONNECTED

    def connect_camera(self) -> None:
        self.camera_state = CameraState.CONNECTING
        self.current_capture_source = self.config.capture_source
        # https://github.com/opencv/opencv/issues/23207
        # https://github.com/opencv/opencv-python/issues/788
        try:
            self.camera.setExceptionMode(True)
            # for some reason explcitly setting the backend allows functions to actually throw exceptions and
            # return from timeouts. this is a very dirty hack so we dont deadlock ourselves when a camera isnt immediately found.
            # although this doesnt really fix the problem with `get_camera_image()` it does make it so that we can at least
            # detect when a camera is disconnected and reconnect to it.
            self.camera.open(self.current_capture_source, cv2.CAP_FFMPEG)
            if self.camera.isOpened():
                self.camera_state = CameraState.CONNECTED
                logger.info("Camera connected!")
            else:
                raise cv2.error
        except (cv2.error, Exception):
            self.camera_state = CameraState.DISCONNECTED
            logger.info(f"Capture source {self.current_capture_source} not found, retrying")

    def get_camera_image(self) -> None:
        # Be warned this is fucked beyond comprehension, if the capture source is dropped `self.camera.read()` wont
        # return for a very long time essentially soft lock the thread for around 30 seconds each time it is called
        # as far as I can tell our code is fine and that this is most likely a bug within OpenCV itself...
        # A dirty hack to fix this might be to just ping the host to see if it is alive before retrieving a new frame
        # A more reasonable solution might be to spawn a new thread with the sole purpose of retrieving the frame
        # doing this will allow us to set a timeout for fetching the frame, so we don't soft-lock the main capture thread
        # but that's a problem for someone else in the future because I get nightmares whenever I look at this capture code
        try:
            ret, frame = self.camera.read()
            if not ret:
                self.camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
                logger.warning("Capture source problem, assuming camera disconnected, waiting for reconnect.")
                self.camera_state = CameraState.DISCONNECTED
                return
            # https://stackoverflow.com/questions/33573312/non-integer-frame-numbers-in-opencv
            frame_number: float = self.camera.get(cv2.CAP_PROP_POS_FRAMES)
            fps: float = self.camera.get(cv2.CAP_PROP_FPS)
            self.push_image_to_queue(frame, frame_number, fps)
        except (cv2.error, Exception):
            self.camera_state = CameraState.DISCONNECTED
            logger.warning("Failed to retrieve or push frame to queue, Assuming camera disconnected, waiting for reconnect.")

    def push_image_to_queue(self, frame: cv2.Mat, frame_number: float, fps: float) -> None:
        qsize: int = self.image_queue.qsize()
        if qsize > 1:
            # logger.warning(f"CAPTURE QUEUE BACKPRESSURE OF {qsize}. CHECK FOR CRASH OR TIMING ISSUES IN ALGORITHM.")
            pass
        try:
            self.image_queue.put(frame)
            # self.image_queue.put((frame, frame_number, fps)) 
        except (Exception):
            logger.exception("Failed to push to camera capture queue!")
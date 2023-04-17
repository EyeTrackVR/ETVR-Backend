import threading
import queue
from .config import AlgorithmConfig
from .types import EyeID
from .logger import get_logger

logger = get_logger()


class EyeProcessor:
    def __init__(self, image_queue: queue.Queue, config: AlgorithmConfig, eye_id: EyeID):
        self.image_queue: queue.Queue = image_queue
        self.config: AlgorithmConfig = config
        self.eye_id: EyeID = eye_id
        # Threading stuff
        self.cancellation_event: threading.Event = threading.Event()
        self.thread: threading.Thread = threading.Thread()

    def __del__(self):
        if self.thread.is_alive():
            self.stop()

    def is_alive(self) -> bool:
        return self.thread.is_alive()
    
    def start(self) -> None:
        # don't start a thread if one already exists
        if self.thread.is_alive():
            logger.debug(f"Thread `{self.thread.name}` requested to start but is already running")
            return

        logger.info(f"Starting thread `EyeProcessor {str(self.eye_id.name).capitalize()}`")
        # clear cancellation event incase thread was stopped in the past
        self.cancellation_event.clear()
        # We need to recreate the thread because it is not possible to start a thread that has already been stopped
        self.thread = threading.Thread(target=self.__run, name=f"EyeProcessor {str(self.eye_id.name).capitalize()}")
        self.thread.start()

    def stop(self) -> None:
        # can't kill a non-existent thread
        if not self.thread.is_alive():
            logger.debug("Request to kill dead thread was made!")
            return

        logger.info(f"Stopping thread `{self.thread.name}`")
        self.cancellation_event.set()
        self.thread.join(timeout=5)
        # If the thread fails to stop, start yelling at the top of your lungs and happy debugging!
        if self.thread.is_alive():
            logger.error(f"Failed to stop thread `{self.thread.name}`!!!!!!!!")

    def restart(self) -> None:
        self.stop()
        self.start()

    def __run(self) -> None:
        while True:
            if self.cancellation_event.is_set():
                return
        
            try:
                current_frame = self.image_queue.get(block=True, timeout=0.1)
            except queue.Empty:
                continue
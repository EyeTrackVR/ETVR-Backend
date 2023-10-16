from queue import Queue
from .types import EyeData
from cv2.typing import MatLike
from .logger import get_logger
from app.utils import clear_queue
from .config import EyeTrackConfig
from multiprocessing.managers import SyncManager
from app.processes import EyeProcessor, Camera, VRChatOSC

logger = get_logger()


# TODO: when we start to integrate babble this should become a common interface that eye trackers and mouth trackers inherit from
class Tracker:
    def __init__(self, config: EyeTrackConfig, uuid: str, manager: SyncManager):
        self.uuid = uuid
        self.config = config
        self.track_config = config.get_tracker_by_uuid(uuid)
        # IPC stuff
        self.manager = manager
        self.osc_queue: Queue[EyeData] = self.manager.Queue()
        self.image_queue: Queue[MatLike] = self.manager.Queue()
        # processes
        self.osc_sender = VRChatOSC(self.config, self.osc_queue)
        self.camera = Camera(self.track_config, self.image_queue)
        self.eye_processor = EyeProcessor(self.track_config, self.image_queue, self.osc_queue)

    def start(self) -> None:
        self.camera.start()
        self.osc_sender.start()
        self.eye_processor.start()

    def stop(self) -> None:
        self.camera.stop()
        self.osc_sender.stop()
        self.eye_processor.stop()
        # if we dont do this we memory leak :3
        clear_queue(self.osc_queue)
        clear_queue(self.image_queue)

    def restart(self) -> None:
        self.camera.restart()
        self.osc_sender.restart()
        self.eye_processor.restart()

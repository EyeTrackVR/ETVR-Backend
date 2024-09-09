from queue import Queue
from fastapi import APIRouter
from .types import EyeData
from cv2.typing import MatLike
from .utils import clear_queue
from .config import EyeTrackConfig
from .visualizer import Visualizer
from multiprocessing.managers import SyncManager
from .processes import EyeProcessor, Camera, VRChatOSC


# TODO: when we start to integrate babble this should become a common interface that eye trackers and mouth trackers inherit from
class Tracker:
    def __init__(self, config: EyeTrackConfig, uuid: str, manager: SyncManager, router: APIRouter):
        self.uuid = uuid
        self.router = router
        self.config = config
        self.tracker_config = config.get_tracker_by_uuid(uuid)
        # IPC stuff
        self.manager = manager
        self.osc_queue: Queue[EyeData] = self.manager.Queue(maxsize=60)
        self.image_queue: Queue[MatLike] = self.manager.Queue(maxsize=60)
        # Used purely for visualization in the frontend
        self.camera_queue: Queue[MatLike] = self.manager.Queue(maxsize=15)
        self.algo_frame_queue: Queue[MatLike] = self.manager.Queue(maxsize=15)
        # processes
        self.processor = EyeProcessor(self.tracker_config, self.image_queue, self.osc_queue, self.algo_frame_queue)
        self.camera = Camera(self.tracker_config, self.image_queue, self.camera_queue)
        self.osc_sender = VRChatOSC(self.osc_queue, self.tracker_config.name)
        # Visualization
        self.camera_visualizer = Visualizer(self.camera_queue)
        self.algorithm_visualizer = Visualizer(self.algo_frame_queue)

    def start(self) -> None:
        self.osc_sender.start()
        self.processor.start()
        self.camera.start()

    def stop(self) -> None:
        self.camera.stop()
        self.processor.stop()
        self.osc_sender.stop()
        self.camera_visualizer.stop()
        self.algorithm_visualizer.stop()
        # if we dont do this we memory leak :3
        clear_queue(self.osc_queue)
        clear_queue(self.image_queue)
        clear_queue(self.camera_queue)
        clear_queue(self.algo_frame_queue)

    def restart(self) -> None:
        self.camera.restart()
        self.osc_sender.restart()
        self.processor.restart()

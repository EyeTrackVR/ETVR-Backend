from multiprocessing import Queue
from .config import EyeTrackConfig
from .logger import get_logger
from .tracker import Tracker
from .osc import VRChatOSCReceiver, VRChatOSC
from fastapi import APIRouter
from .types import EyeID, EyeData

logger = get_logger()

# might be temporary, not sure if we are gonna use something else for IPC
# TODO: talk to Zanzy / lorrow about this!
class ETVR:
    def __init__(self):
        self.config: EyeTrackConfig = EyeTrackConfig()
        self.config.load()
        # OSC stuff
        self.osc_queue: Queue[EyeData] = Queue()
        self.osc_sender: VRChatOSC = VRChatOSC(self.config, self.osc_queue)
        self.osc_receiver: VRChatOSCReceiver = VRChatOSCReceiver(self.config)
        # Trackers
        self.tracker_left: Tracker = Tracker(EyeID.LEFT, self.config, self.osc_queue)
        self.tracker_right: Tracker = Tracker(EyeID.RIGHT, self.config, self.osc_queue)
        # Object for fastapi routes
        self.router: APIRouter = APIRouter()

    def __del__(self):
        self.stop()

    def add_routes(self) -> None:
        logger.debug("Adding routes to ETVR")
        # config stuff
        self.router.add_api_route("/etvr/config", self.config.update, methods=["POST"])
        self.router.add_api_route("/etvr/config", self.config.return_config, methods=["GET"])
        # general stuff
        self.router.add_api_route("/etvr/start", self.start, methods=["GET"])
        self.router.add_api_route("/etvr/stop", self.stop, methods=["GET"])
        self.router.add_api_route("/etvr/restart", self.restart, methods=["GET"])
        # camera stuff
        self.router.add_api_route("/etvr/camera_l/status", self.tracker_left.camera.get_status, methods=["GET"])
        self.router.add_api_route("/etvr/camera_r/status", self.tracker_right.camera.get_status, methods=["GET"])

    def start(self) -> None:
        logger.debug("Starting...")
        self.tracker_left.start()
        self.tracker_right.start()
        self.osc_sender.start()
        self.osc_receiver.start()

    def stop(self) -> None:
        logger.debug("Stopping...")
        self.tracker_left.stop()
        self.tracker_right.stop()
        self.osc_sender.stop()
        self.osc_receiver.stop()

    def restart(self) -> None:
        self.stop()
        self.start()

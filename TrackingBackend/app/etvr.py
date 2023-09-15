from .config import EyeTrackConfig
from .logger import get_logger
from .tracker import Tracker
from app.processes import VRChatOSCReceiver, VRChatOSC
from multiprocessing import Manager
from queue import Queue
from fastapi import APIRouter
from .types import EyeData
from app.utils import clear_queue

logger = get_logger()


class ETVR:
    def __init__(self):
        self.config: EyeTrackConfig = EyeTrackConfig()
        self.config.load()
        self.running: bool = False
        # IPC stuff
        self.manager = Manager()
        self.osc_queue: Queue[EyeData] = self.manager.Queue()
        # OSC stuff
        self.osc_sender = VRChatOSC(self.config, self.osc_queue)
        self.osc_receiver = VRChatOSCReceiver(self.config)
        # Trackers
        self.trackers: list[Tracker] = []
        self.setup_trackers()
        # Object for fastapi routes
        self.router: APIRouter = APIRouter()

    def setup_trackers(self) -> None:
        logger.debug("Setting up trackers")
        for tracker in self.trackers:
            tracker.stop()

        self.trackers.clear()
        for tracker_config in self.config.trackers:
            if tracker_config.enabled:
                self.trackers.append(Tracker(tracker_config, self.osc_queue, self.manager))

    def add_routes(self) -> None:
        logger.debug("Adding routes to ETVR")
        # config stuff
        self.router.add_api_route("/etvr/config", self.config.update, methods=["POST"])
        self.router.add_api_route("/etvr/config", self.config.return_config, methods=["GET"])
        self.router.add_api_route("/etvr/config/tracker", self.config.create_tracker, methods=["put"])
        self.router.add_api_route("/etvr/config/tracker", self.config.update_tracker, methods=["post"])
        self.router.add_api_route("/etvr/config/tracker", self.config.delete_tracker, methods=["delete"])
        self.router.add_api_route("/etvr/config/tracker", self.config.get_tracker_by_uuid, methods=["get"])
        self.router.add_api_route("/etvr/config/save", self.config.save, methods=["GET"])
        self.router.add_api_route("/etvr/config/load", self.config.load, methods=["GET"])
        # general stuff
        self.router.add_api_route("/etvr/start", self.start, methods=["GET"])
        self.router.add_api_route("/etvr/stop", self.stop, methods=["GET"])
        self.router.add_api_route("/etvr/restart", self.restart, methods=["GET"])
        self.router.add_api_route("/etvr/status", lambda: self.running, methods=["GET"])

    def start(self) -> None:
        logger.debug("Starting...")
        # TODO: we should have a endpoint to start individual trackers
        for tracker in self.trackers:
            tracker.start()
        self.osc_sender.start()
        self.osc_receiver.start()
        self.running = True

    def stop(self) -> None:
        logger.debug("Stopping...")
        # TODO: we should have a endpoint to stop individual trackers
        for tracker in self.trackers:
            tracker.stop()
        self.osc_sender.stop()
        self.osc_receiver.stop()
        clear_queue(self.osc_queue)
        self.running = False

    def restart(self) -> None:
        self.stop()
        self.start()

from app.processes import VRChatOSCReceiver, VRChatOSC
from multiprocessing import Manager
from .config import EyeTrackConfig
from app.utils import clear_queue
from .logger import get_logger
from fastapi import APIRouter
from .tracker import Tracker
from .types import EyeData
from queue import Queue

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

    def add_routes(self) -> None:
        logger.debug("Adding routes to ETVR")
        # region: General Endpoints
        self.router.add_api_route(
            name="Start ETVR",
            path="/etvr/start",
            endpoint=self.start,
            methods=["GET"],
            tags=["default"],
            description="""
            Start the ETVR backend, this will start all enabled trackers and the OSC sender / receiver.
            """,
        )
        self.router.add_api_route(
            name="Stop ETVR",
            path="/etvr/stop",
            endpoint=self.stop,
            methods=["GET"],
            tags=["default"],
            description="""
            Stop the ETVR backend, this will stop all trackers and the OSC sender / receiver.
            """,
        )
        self.router.add_api_route(
            name="Restart ETVR",
            path="/etvr/restart",
            endpoint=self.restart,
            methods=["GET"],
            tags=["default"],
            description="""
            Restart the ETVR backend, internally this just calls stop and then start.
            """,
        )
        self.router.add_api_route(
            name="Return ETVR Status",
            path="/etvr/status",
            endpoint=lambda: self.running,
            methods=["GET"],
            tags=["default"],
            description="""
            Return the current status, True if ETVR is running, False if not.
            """,
        )
        # endregion

        # region: Config Endpoints
        self.router.add_api_route(
            name="Update Config",
            path="/etvr/config",
            endpoint=self.config.update,
            methods=["POST"],
            tags=["Config"],
            description="""
            Update the current config, partial updates are allowed (only the fields you want to update need to be provided)
            """,
        )
        self.router.add_api_route(
            name="Return Config",
            path="/etvr/config",
            endpoint=self.config.return_config,
            methods=["GET"],
            tags=["Config"],
            description="""
            Return the currently loadeed config
            """,
        )
        self.router.add_api_route(
            name="Save Config",
            path="/etvr/config/save",
            endpoint=self.config.save,
            tags=["Config"],
            methods=["GET"],
            description="""
            Save the current config to a file.
            """,
        )
        self.router.add_api_route(
            name="Load Config",
            path="/etvr/config/load",
            endpoint=self.config.load,
            methods=["GET"],
            tags=["Config"],
            description="""
            Load a config from a file.
            """,
        )
        self.router.add_api_route(
            name="Reset Config",
            path="/etvr/config/reset",
            endpoint=self.config.reset,
            methods=["GET"],
            tags=["Config"],
            description="""
            Reset the config to the default values.
            """,
        )
        # endregion

        # region: Tracker Config Endpoints
        self.router.add_api_route(
            name="Reset a trackers config",
            path="/etvr/config/tracker/reset",
            endpoint=self.config.reset_tracker,
            methods=["GET"],
            tags=["Tracker Config"],
            description="""
            Reset a tracker's config to the default values. (tracker uuid and name will remain the same)
            """,
        )
        self.router.add_api_route(
            name="Return all tracker configs",
            path="/etvr/config/trackers",
            endpoint=self.config.get_trackers,
            methods=["GET"],
            tags=["Tracker Config"],
            description="""
            Return a list of all trackers with their configs.
            """,
        )
        self.router.add_api_route(
            name="Return a trackers config",
            path="/etvr/config/tracker",
            endpoint=self.config.get_tracker_by_uuid,
            methods=["GET"],
            tags=["Tracker Config"],
            description="""
            Get a tracker's config with a given uuid.
            """,
        )
        self.router.add_api_route(
            name="Create a new tracker",
            path="/etvr/config/tracker",
            endpoint=self.config.create_tracker,
            methods=["PUT"],
            tags=["Tracker Config"],
            description="""
            Create a new tracker, if no config is provided, a default config will be used.
            """,
        )
        self.router.add_api_route(
            name="Update a trackers config",
            path="/etvr/config/tracker",
            endpoint=self.config.update_tracker,
            methods=["POST"],
            tags=["Tracker Config"],
            description="""
            Update a tracker with a given uuid, partial updates are allowed (only the fields you want to update need to be provided)
            """,
        )
        self.router.add_api_route(
            name="Delete a tracker",
            path="/etvr/config/tracker",
            endpoint=self.config.delete_tracker,
            methods=["DELETE"],
            tags=["Tracker Config"],
            description="""
            Delete a tracker with a given uuid.
            """,
        )
        # endregion

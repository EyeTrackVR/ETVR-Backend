from .config import EyeTrackConfig
from .logger import get_logger
import queue
import threading
from pythonosc import udp_client, osc_server, dispatcher
logger = get_logger()

# ----------------------------------------------------------------------------------------------------------------------
#   TODO: Might be worth having the classes spawn its own thread so it is able to "restart" on config change
#   Currently to change what port / address is used you would having to kill the Thread and remake it but with this
#   method we would only need to call .restart() and all the magic can be handled behind the scenes
# ----------------------------------------------------------------------------------------------------------------------


class VRChatOSC:
    def __init__(self, config: EyeTrackConfig, msg_queue: queue.Queue[tuple[bool, int, int]]):
        self.main_config = config
        self.config = config.osc
        self.msg_queue = msg_queue
        self.client = udp_client.SimpleUDPClient(self.config.address, self.config.sending_port)
        # Threading stuff
        self.cancellation_event: threading.Event = threading.Event()
        self.thread: threading.Thread = threading.Thread()

    def start(self) -> None:
        # don't start a thread if one already exists
        if self.thread.is_alive():
            logger.debug(f"Thread requested to start but is already running")
            return

        logger.info("Starting OSC thread")
        # clear cancellation event incase thread was stopped in the past
        self.cancellation_event.clear()
        # We need to recreate the thread because it is not possible to start a thread that has already been stopped
        self.thread = threading.Thread(target=self.__run, name="OSC")
        self.thread.start()

    def stop(self) -> None:
        # can't kill a non-existent thread
        if not self.thread.is_alive():
            logger.debug("Request to kill dead thread was made!")
            return

        logger.info("Stopping OSC thread")
        self.cancellation_event.set()
        self.thread.join(timeout=5)
        # If the thread fails to stop, start yelling at the top of your lungs and happy debugging!
        if self.thread.is_alive():
            logger.error(f"Failed to stop OSC thread!!!!!!!!")

    def restart(self) -> None:
        self.stop()
        self.start()

    def __run(self) -> None:
        while True:
            if self.cancellation_event.is_set():
                return


# TODO: Once more stuff is working events for centering and calibration needs to be bound
class VRChatOSCReceiver:
    def __init__(self, config: EyeTrackConfig):
        self.main_config = config
        self.config = config.osc
        self.dispatcher = dispatcher.Dispatcher()
        self.bad_init: bool = False
        try:
            self.server = osc_server.OSCUDPServer((self.config.address, self.config.receiver_port), self.dispatcher)
        except OSError:
            logger.error(f"OSC Receive port: {self.config.receiver_port} is occupied!")
            self.bad_init = True

    def start(self) -> None:
        pass

    def stop(self) -> None:
        self.server.shutdown()

    def restart(self) -> None:
        self.stop()
        self.restart()

    def run(self) -> None:
        if self.config.enable_receiving and not self.bad_init:
            try:
                logger.info(f"VRChatOSCReceiver sering on {self.config.address}:{self.config.receiver_port}")
                self.server.serve_forever()
            except OSError:
                logger.exception("Failed to start OSCReceiver")
                return
        else:
            logger.debug("Skipping VRChatOSCReceiver.run(), either a bad init occurred or it is disabled!")

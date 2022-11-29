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
    def __int__(self, config: EyeTrackConfig, msg_queue: queue.Queue[tuple[bool, int, int]], cancellation_event: threading.Event):
        self.main_config = config
        self.config = config.osc
        self.msg_queue = msg_queue
        self.cancellation_event = cancellation_event
        self.client = udp_client.SimpleUDPClient(self.config.address, self.config.sending_port)

    def __run(self):
        while True:
            if self.cancellation_event.is_set():
                logger.info("Exiting OSC queue")
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

    def shutdown(self):
        self.server.shutdown()

    def run(self):
        if self.config.enable_receiving and not self.bad_init:
            try:
                logger.info(f"VRChatOSCReceiver sering on {self.config.address}:{self.config.receiver_port}")
                self.server.serve_forever()
            except OSError:
                logger.exception("Failed to start OSCReceiver")
                return
        else:
            logger.info("Skipping VRChatOSCReceiver.run(), `enable_receiving` is false")

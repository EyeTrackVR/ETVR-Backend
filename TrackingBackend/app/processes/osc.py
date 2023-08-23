from __future__ import annotations
from app.config import EyeTrackConfig, OSCConfig
from app.utils import WorkerProcess
from app.types import EyeData, EyeID
from app.logger import get_logger
from queue import Queue
import threading
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_server import ThreadingOSCUDPServer


logger = get_logger()


class VRChatOSC(WorkerProcess):
    def __init__(self, config: EyeTrackConfig, osc_queue: Queue[EyeData]):
        super().__init__(name="VRChat OSC")
        # Synced variables
        self.osc_queue: Queue[EyeData] = osc_queue
        # Unsynced variables
        self.config: EyeTrackConfig = config
        self.client = SimpleUDPClient(self.config.osc.address, self.config.osc.sending_port)

    # TODO: Since vrchat implements OSCQuery shouldnt rely on the config for this
    # and instead use the OSCQuery to address and port for vrc
    def startup(self) -> None:
        pass

    def run(self) -> None:
        try:
            eye_data: EyeData = self.osc_queue.get(block=True, timeout=0.5)
            if not self.config.osc.enable_sending:
                return
        except Exception:
            return

        if self.config.osc.mirror_eyes:
            self.client.send_message(self.config.osc.endpoints.eyes_y, float(eye_data.y))
            self.client.send_message(self.config.osc.endpoints.left_eye_x, float(eye_data.x))
            self.client.send_message(self.config.osc.endpoints.right_eye_x, float(eye_data.x))
            self.client.send_message(self.config.osc.endpoints.left_eye_blink, float(eye_data.blink))
            self.client.send_message(self.config.osc.endpoints.right_eye_blink, float(eye_data.blink))
            return

        if eye_data.eye_id == EyeID.LEFT:
            self.client.send_message(self.config.osc.endpoints.eyes_y, float(eye_data.y))
            self.client.send_message(self.config.osc.endpoints.left_eye_x, float(eye_data.x))
            self.client.send_message(self.config.osc.endpoints.left_eye_blink, float(eye_data.blink))
        elif eye_data.eye_id == EyeID.RIGHT:
            self.client.send_message(self.config.osc.endpoints.eyes_y, float(eye_data.y))
            self.client.send_message(self.config.osc.endpoints.right_eye_x, float(eye_data.x))
            self.client.send_message(self.config.osc.endpoints.right_eye_blink, float(eye_data.blink))

    def shutdown(self) -> None:
        pass

    def on_config_update(self, config: EyeTrackConfig) -> None:
        self.config = config


# TODO: refactor this
class VRChatOSCReceiver:
    def __init__(self, config: EyeTrackConfig):
        self.main_config: EyeTrackConfig = config
        self.endpoints = config.osc.endpoints
        self.config: OSCConfig = config.osc
        self.dispatcher: Dispatcher = Dispatcher()
        self.server: ThreadingOSCUDPServer = ThreadingOSCUDPServer((self.config.address, self.config.receiver_port), self.dispatcher)
        self.thread: threading.Thread = threading.Thread()

    def __del__(self):
        if self.thread.is_alive():
            self.stop()

    def is_alive(self) -> bool:
        return self.thread.is_alive()

    def recalibrate_eyes(self, address, osc_value) -> None:
        pass

    def recenter_eyes(self, address, osc_value) -> None:
        pass

    def toggle_sync_blink(self, address, osc_value) -> None:
        self.config.sync_blink = not self.config.sync_blink

    def map_events(self) -> None:
        self.dispatcher.map(self.endpoints.recalibrate, self.recalibrate_eyes)
        self.dispatcher.map(self.endpoints.recenter, self.recenter_eyes)
        self.dispatcher.map(self.endpoints.sync_blink, self.toggle_sync_blink)

    def start(self) -> None:
        # don't start a thread if one already exists
        if self.thread.is_alive():
            logger.debug(f"Thread `{self.thread.name}` requested to start but is already running")
            return

        logger.info("Starting OSC receiver thread")
        # we redefine the OSC server here just incase the address or port changed
        self.server.socket.close()  # close the old socket so we don't get a "address already in use" error
        self.server = ThreadingOSCUDPServer((self.config.address, self.config.receiver_port), self.dispatcher)
        logger.info(f"OSC receiver listening on {self.config.address}:{self.config.receiver_port}")
        self.map_events()
        self.thread = threading.Thread(target=self.server.serve_forever, name="OSC Receiver")
        self.thread.start()

    def stop(self) -> None:
        if not self.thread.is_alive():
            logger.debug("Request to kill dead thread was made!")
            return

        logger.info("Stopping OSC receiver thread")
        self.server.shutdown()
        self.thread.join(timeout=5)
        # If the thread fails to stop, start yelling at the top of your lungs and happy debugging!
        if self.thread.is_alive():
            logger.error("Failed to stop OSC receiver thread!!!!!!!!")

    def restart(self) -> None:
        self.stop()
        self.restart()

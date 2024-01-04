from app.utils import WorkerProcess, OneEuroFilter
from app.config import EyeTrackConfig, OSCConfig
from app.types import EyeData, TrackerPosition
from app.logger import get_logger
from queue import Queue, Empty
from copy import deepcopy
from typing import Final
import numpy as np
import threading
import cv2
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_server import ThreadingOSCUDPServer

WIDTH: Final = 256
HEIGHT: Final = 256

logger = get_logger()


class VRChatOSC(WorkerProcess):
    def __init__(self, osc_queue: Queue[EyeData], name: str):
        super().__init__(name=f"OSC {name}")
        # Synced variables
        self.osc_queue: Queue[EyeData] = osc_queue
        # Unsynced variables
        self.config: EyeTrackConfig = self.base_config
        self.client = SimpleUDPClient(self.config.osc.address, self.config.osc.sending_port)
        self.filter = OneEuroFilter(np.random.rand(2), 0.9, 5.0)

    # TODO: Since vrchat implements OSCQuery we shouldnt rely on the config for this
    # we should instead query the server for the endpoints
    def startup(self) -> None:
        pass

    def run(self) -> None:
        try:
            eye_data: EyeData = self.osc_queue.get(block=True, timeout=0.5)
            if not self.config.osc.enable_sending:
                return

            self.smooth(eye_data)
            # "normalize" the data to be between -1 and 1
            eye_data.y = -(2 * (eye_data.y - 0.5))
            # flip output for right eye to account for perspective
            if eye_data.position == TrackerPosition.RIGHT_EYE:
                eye_data.x = 2 * (eye_data.x - 0.5)
            elif eye_data.position == TrackerPosition.LEFT_EYE:
                eye_data.x = -(2 * (eye_data.x - 0.5))
        except Empty:
            return
        except Exception:
            self.logger.exception("Failed to get eye data from queue")
            return

        if self.config.osc.mirror_eyes:
            self.client.send_message(self.config.osc.endpoints.eyes_y, float(eye_data.y))
            self.client.send_message(self.config.osc.endpoints.left_eye_x, float(eye_data.x))
            self.client.send_message(self.config.osc.endpoints.right_eye_x, float(eye_data.x))
            self.client.send_message(self.config.osc.endpoints.left_eye_blink, float(eye_data.blink))
            self.client.send_message(self.config.osc.endpoints.right_eye_blink, float(eye_data.blink))
            return

        if eye_data.position == TrackerPosition.LEFT_EYE:
            self.client.send_message(self.config.osc.endpoints.eyes_y, float(eye_data.y))
            self.client.send_message(self.config.osc.endpoints.left_eye_x, float(eye_data.x))
            self.client.send_message(self.config.osc.endpoints.left_eye_blink, float(eye_data.blink))
        elif eye_data.position == TrackerPosition.RIGHT_EYE:
            self.client.send_message(self.config.osc.endpoints.eyes_y, float(eye_data.y))
            self.client.send_message(self.config.osc.endpoints.right_eye_x, float(eye_data.x))
            self.client.send_message(self.config.osc.endpoints.right_eye_blink, float(eye_data.blink))

    def shutdown(self) -> None:
        pass

    def on_config_update(self, config: EyeTrackConfig) -> None:
        self.config = config

    def smooth(self, data: EyeData) -> EyeData:
        original = deepcopy(data)
        data.x, data.y = self.filter(np.array([data.x, data.y]))
        self.draw_debug("Smoothed", original, data)
        return data

    def draw_debug(self, window: str, original: EyeData, smoothed: EyeData) -> None:
        frame = np.zeros((HEIGHT, WIDTH, 3), np.uint8)
        frame[:] = (255, 255, 255)
        x1 = int(original.x * WIDTH)
        y1 = int(original.y * HEIGHT)
        x2 = int(smoothed.x * WIDTH)
        y2 = int(smoothed.y * HEIGHT)
        cv2.circle(frame, (x1, y1), 5, (0, 0, 255), -1)
        cv2.circle(frame, (x2, y2), 5, (255, 0, 0), -1)
        cv2.putText(frame, "original", (0, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1)
        cv2.putText(frame, "smoothed", (0, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 1)
        self.window.imshow(self.process_name(), frame)


# TODO: refactor this
class VRChatOSCReceiver:
    def __init__(self, config: EyeTrackConfig):
        self.main_config: EyeTrackConfig = config
        self.endpoints = config.osc.endpoints
        self.config: OSCConfig = config.osc
        # FIXME: this is a hack
        if self.config.enable_receiving:
            self.dispatcher: Dispatcher = Dispatcher()
            self.server: ThreadingOSCUDPServer = ThreadingOSCUDPServer(
                (self.config.address, self.config.receiver_port), self.dispatcher
            )
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
        if self.config.enable_receiving:
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
        else:
            logger.info("OSC receiver is disabled, skipping start")

    def stop(self) -> None:
        if self.config.enable_receiving:
            if not self.thread.is_alive():
                logger.debug("Request to kill dead thread was made!")
                return

            logger.info("Stopping OSC receiver thread")
            self.server.shutdown()
            self.thread.join(timeout=5)
            # If the thread fails to stop, start yelling at the top of your lungs and happy debugging!
            if self.thread.is_alive():
                logger.error("Failed to stop OSC receiver thread!!!!!!!!")
        else:
            logger.info("OSC receiver is disabled, skipping stop")

    def restart(self) -> None:
        self.stop()
        self.restart()

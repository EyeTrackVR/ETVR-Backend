from app.camera import Camera
import queue
from app.logger import get_logger, setup_logger
from app.config import EyeTrackConfig
import cv2
import time
setup_logger()

config = EyeTrackConfig()
config.load()
print(config.dict())
config.update({
    'version': 3,
    'osc': {
        'address': 'localhost',
        'sync_blink': True
    }
})
print(config.dict())
config.save()
image_queue = queue.Queue()
cam = Camera(config.left_eye, image_queue)
cam.start()


while True:
    frame = image_queue.get()
    cv2.imshow("Poes", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cv2.destroyAllWindows()
cam.stop()
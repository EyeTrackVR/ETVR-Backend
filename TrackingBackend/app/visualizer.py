# FIXME: this sucks and is slow, it doesnt even work, and it blocks the event loop.
import cv2
from queue import Queue
from fastapi.responses import StreamingResponse

OFLINE_IMAGE = cv2.imread("assets/CameraOffline.png")

class Visualizer:
    def __init__(self, image_queue: Queue, remove_from_queue: bool = False):
        self.image_queue: Queue = image_queue
        self.remove_from_queue: bool = remove_from_queue
        print("YOU ARE MAKING A MISTAKE DONT USE THIS CLASS")
        assert False

    async def gen_frame(self):
        while True:
            if self.remove_from_queue:
                frame = self.image_queue.get()
            else:
                frame = self.image_queue.queue[0]

            ret, frame = cv2.imencode(".jpg", frame)
            if not ret:
                continue
            frame = frame.tobytes()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            # sleep so we dont block the event loop
            # await asyncio.sleep(0.01)


    async def video_feed(self):
        return StreamingResponse(self.gen_frame(), media_type="multipart/x-mixed-replace; boundary=frame")

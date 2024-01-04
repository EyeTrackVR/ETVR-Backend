import cv2
from typing import Any
from queue import Queue
from fastapi.responses import StreamingResponse

OFLINE_IMAGE = cv2.imread("assets/images/camera_offline.png")


class Visualizer:
    def __init__(self, image_queue: Queue):
        self.image_queue: Queue = image_queue

    def gen_frame(self):
        while True:
            try:
                frame = self.image_queue.get(timeout=1)
            except Exception:
                frame = OFLINE_IMAGE
            ret, frame = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + bytearray(frame) + b"\r\n")

    def video_feed(self) -> StreamingResponse:
        return StreamingResponse(self.gen_frame(), media_type="multipart/x-mixed-replace; boundary=frame")

    def __call__(self, *args: Any, **kwds: Any) -> StreamingResponse:
        return self.video_feed()

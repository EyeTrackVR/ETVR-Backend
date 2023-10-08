import cv2
from app.types import TrackerPosition, EyeData
from queue import Queue, Empty


def clamp(x, low, high):
    return max(low, min(x, high))


def clear_queue(queue: Queue) -> None:
    while True:
        try:
            queue.get(block=True, timeout=0.1)
        except Empty:
            break


# Base class for all algorithms
class BaseAlgorithm:
    # all algorithms must implement this method
    def run(self, frame: cv2.Mat) -> EyeData:
        return EyeData(0, 0, 0, TrackerPosition.UNDEFINED)

    def normalize(self, x: float, y: float, width: int, height: int) -> tuple[float, float]:
        """takes a point and normalizes it to a range of 0 to 1"""
        tx: float = x / width
        ty: float = y / height

        return tx, ty

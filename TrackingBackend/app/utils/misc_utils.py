from app.types import EyeData, TRACKING_FAILED
from queue import Queue, Empty
from cv2.typing import MatLike


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
    def run(self, frame: MatLike) -> EyeData:
        return TRACKING_FAILED

    def normalize(self, x: float, y: float, width: int, height: int) -> tuple[float, float]:
        """takes a point and normalizes it to a range of 0 to 1"""
        tx: float = x / width
        ty: float = y / height

        return tx, ty

    def get_name(self) -> str:
        return self.__class__.__name__

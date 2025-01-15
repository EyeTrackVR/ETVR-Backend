from ..types import EyeData, TrackerPosition, TRACKING_FAILED, EMPTY_FRAME
from queue import Queue, Empty
from cv2.typing import MatLike


def is_serial(source: str) -> bool:
    serial_prefixes = ["com", "/dev/tty", "/dev/serial"]
    return any(source.lower().startswith(prefix) for prefix in serial_prefixes)


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
    def run(self, frame: MatLike, tracker_position: TrackerPosition) -> tuple[EyeData, MatLike]:
        return TRACKING_FAILED, EMPTY_FRAME

    def normalize(self, x: float, y: float, width: int, height: int) -> tuple[float, float]:
        """takes a point and normalizes it to a range of 0 to 1"""
        tx: float = x / width
        ty: float = y / height

        return tx, ty

    def get_name(self) -> str:
        return self.__class__.__name__


def mask_to_cpu_list(cpu_mask: str) -> list[int]:
    """Converts a hex mask to a list of cpu ids"""
    cpu_list: list[int] = []
    if cpu_mask != "":
        mask = int(cpu_mask, 16)

        bit_position = 0
        while mask > 0:
            if mask & 1:
                cpu_list.append(bit_position)
            mask >>= 1
            bit_position += 1

    return cpu_list

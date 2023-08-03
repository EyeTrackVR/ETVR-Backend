import cv2
from app.types import EyeID, EyeData


def clamp(x, low, high):
    return max(low, min(x, high))


# Base class for all algorithms
class BaseAlgorithm:
    # all algorithms must implement this method
    def run(self, frame: cv2.Mat, eye_id: EyeID) -> EyeData:
        return EyeData(0, 0, 0, eye_id)

    # takes a point and normalizes it to a range of -1 to 1
    def normalize(self, x: float, y: float, width: int, height: int) -> tuple[float, float]:
        tx: float = x / width
        ty: float = y / height

        tx = 2 * (tx - 0.5)
        ty = 2 * (ty - 0.5)

        return tx, ty

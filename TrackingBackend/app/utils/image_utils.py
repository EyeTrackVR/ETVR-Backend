import cv2
from cv2.typing import MatLike


def mat_crop(x: int, y: int, w: int, h: int, frame: MatLike) -> MatLike:
    if x <= 0 or y <= 0 or w <= 0 or h <= 0:
        return frame
    return frame[y : y + h, x : x + w]


def mat_rotate(frame: MatLike, angle: float, border_color: tuple[int, int, int] = (255, 255, 255)) -> MatLike:
    row, col, _ = frame.shape
    matrix = cv2.getRotationMatrix2D((col / 2, row / 2), angle, 1)
    return cv2.warpAffine(frame, matrix, (col, row), borderMode=cv2.BORDER_CONSTANT, borderValue=border_color)

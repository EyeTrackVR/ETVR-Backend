import cv2
from cv2.typing import MatLike


def safe_crop(frame: MatLike, x: int, y: int, w: int, h: int, keepsize=False):
    frame_h, frame_w = frame.shape[:2]
    outframe = frame[max(0, y) : min(frame_h, h), max(0, x) : min(frame_w, w)].copy()
    reqsize_x, reqsize_y = abs(w - x), abs(h - y)
    if keepsize and outframe.shape[:2] != (reqsize_y, reqsize_x):
        # If the size is different from the expected size (smaller by the amount that is out of range)
        outframe = cv2.resize(outframe, (reqsize_x, reqsize_y))
    return outframe


def mat_crop(x: int, y: int, w: int, h: int, frame: MatLike) -> MatLike:
    if x <= 0 or y <= 0 or w <= 0 or h <= 0:
        return frame
    return frame[y : y + h, x : x + w]


def mat_rotate(frame: MatLike, angle: float, border_color: tuple[int, int, int] = (255, 255, 255)) -> MatLike:
    row, col, _ = frame.shape
    matrix = cv2.getRotationMatrix2D((col / 2, row / 2), angle, 1)
    return cv2.warpAffine(frame, matrix, (col, row), borderMode=cv2.BORDER_CONSTANT, borderValue=border_color)

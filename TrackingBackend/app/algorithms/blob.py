import cv2
from app.processes import EyeProcessor
from app.types import TrackerPosition, EyeData
from app.utils import BaseAlgorithm


class Blob(BaseAlgorithm):
    def __init__(self, eye_processor: EyeProcessor):
        self.ep = eye_processor

    def run(self, frame: cv2.Mat) -> EyeData:
        _, larger_threshold = cv2.threshold(frame, self.ep.config.blob.threshold, 255, cv2.THRESH_BINARY)

        try:
            # Try rebuilding our contours
            contours, _ = cv2.findContours(larger_threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)

            # If we have no contours, we have nothing to blob track. Fail here.
            if len(contours) == 0:
                self.ep.logger.warning(f"Failed to find any contours for {self.ep.tracker_position.name} eye")
                return EyeData(0, 0, 0, TrackerPosition.UNDEFINED)
        except (cv2.error, Exception):
            self.ep.logger.exception("Something went wrong!")
            return EyeData(0, 0, 0, TrackerPosition.UNDEFINED)

        for cnt in contours:
            (x, y, w, h) = cv2.boundingRect(cnt)

            # if our blob width/height are within suitable (yet arbitrary) boundaries, call that good.
            # TODO: This should be scaled based on camera resolution.
            if (
                not self.ep.config.blob.minsize <= h <= self.ep.config.blob.maxsize
                or not self.ep.config.blob.minsize <= w <= self.ep.config.blob.maxsize
            ):
                continue

            cx = x + int(w / 2)
            cy = y + int(h / 2)

            cv2.drawContours(frame, [cnt], -1, (0, 255, 0), 3)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.imshow(str({self.ep.name}), frame)

            tx, ty = self.normalize(cx, cy, frame.shape[0], frame.shape[1])
            return EyeData(tx, ty, 1, self.ep.tracker_position)

        return EyeData(0, 0, 0, TrackerPosition.UNDEFINED)

# ------------------------------------------------------------------------------
# TODO: look at ETVR source and adapt blob stuff better
# ------------------------------------------------------------------------------
import cv2
import numpy as np
from app.types import EyeData
from app.eye_processor import EyeProcessor


class Blob:
    def __init__(self, eye_processor: EyeProcessor):
        self.ep = eye_processor

    def run(self, frame):
        _, larger_threshold = cv2.threshold(frame, (self.ep.config.blob.threshold + 12), 255, cv2.THRESH_BINARY)

        try:
            # Try rebuilding our contours
            contours, _ = cv2.findContours(larger_threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)

            # If we have no contours, we have nothing to blob track. Fail here.
            if len(contours) == 0:
                print("No contours found for image")
                raise RuntimeError("No contours found for image")
        except (cv2.error, Exception):
            pass

        for cnt in contours:
            (x, y, w, h) = cv2.boundingRect(cnt)

            # if our blob width/height are within suitable (yet arbitrary) boundaries, call that good.
            # TODO: This should be scaled based on camera resolution.
            # if not self.ep.config.blob.minsize <= h <= self.ep.config.blob.maxsize or not self.ep.config.blob.minsize <= w <= self.ep.config.blob.maxsize:
            #     break
            
            cx = x + int(w / 2)
            cy = y + int(h / 2)

            cv2.drawContours(frame, [cnt], -1, (0, 255, 0), 3)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            cv2.imshow("Blob", frame)
            cv2.waitKey(1)

            # print(f"Blob found at {cx}, {cy}")
            return cx, cy

        return 0, 0, larger_threshold
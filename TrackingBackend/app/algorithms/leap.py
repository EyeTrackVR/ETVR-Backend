"""
------------------------------------------------------------------------------------------------------

                                            ,@@@@@@
                                        @@@@@@@@@@@            @@@
                                        @@@@@@@@@@@@      @@@@@@@@@@@
                                    @@@@@@@@@@@@@   @@@@@@@@@@@@@@
                                    @@@@@@@/         ,@@@@@@@@@@@@@
                                        /@@@@@@@@@@@@@@@  @@@@@@@@
                                @@@@@@@@@@@@@@@@@@@@@@@@ @@@@@
                            @@@@@@@@                @@@@@
                            ,@@@                        @@@@&
                                            @@@@@@.       @@@@
                                @@@     @@@@@@@@@/      @@@@@
                                ,@@@.     @@@@@@((@     @@@@(
                                //@@@        ,,  @@@@  @@@@@
                                @@@(                @@@@@@@
                                @@@  @          @@@@@@@@#
                                    @@@@@@@@@@@@@@@@@
                                    @@@@@@@@@@@@@(

Leap by: Prohurtz
Algorithm App Implementation By: Prohurtz, ShyAssassin

Copyright (c) 2023 EyeTrackVR <3
This project is licensed under the MIT License. See LICENSE for more details.
------------------------------------------------------------------------------------------------------
"""

import math
import cv2
import numpy as np
import onnxruntime as rt
from app.types import EyeData
from app.processes import EyeProcessor
from app.utils import BaseAlgorithm, OneEuroFilter

rt.disable_telemetry_events()
ONNX_OPTIONS = rt.SessionOptions()
ONNX_OPTIONS.inter_op_num_threads = 1
ONNX_OPTIONS.intra_op_num_threads = 1
ONNX_OPTIONS.graph_optimization_level = rt.GraphOptimizationLevel.ORT_ENABLE_ALL
MODEL_PATH = "assets/leap.onnx"


class Leap(BaseAlgorithm):
    def __init__(self, eye_processor: EyeProcessor) -> None:
        self.ep = eye_processor
        self.openlist: list[float] = []
        self.filter = OneEuroFilter(np.random.rand(7, 2), 0.9, 5.0)
        self.session = rt.InferenceSession(MODEL_PATH, ONNX_OPTIONS, ["CPUExecutionProvider"])
        self.ep.logger.debug(f"Created Inference Session with `{MODEL_PATH}`")

    def run(self, frame: cv2.Mat) -> EyeData:
        pre_landmark = self.filter(self.run_model(frame.copy()))
        self.draw_landmarks(frame, pre_landmark)

        blink = 0.0
        try:
            distance = math.dist(pre_landmark[1], pre_landmark[3])
            if len(self.openlist) < 5000:
                self.openlist.append(distance)
            else:
                self.openlist.pop(0)
                self.openlist.append(distance)

            blink = (distance - max(self.openlist)) / (min(self.openlist) - max(self.openlist))
            blink = 1 - blink
        except Exception:
            self.ep.logger.exception("Failed to calculate eye openness")
            blink = 0.7
        finally:
            if blink <= self.ep.config.leap.blink_threshold:
                blink = 0

        x = pre_landmark[6][0]
        y = pre_landmark[6][1]

        return EyeData(x, y, blink, self.ep.tracker_position)

    def run_model(self, frame) -> np.ndarray:
        frame = cv2.resize(frame, (112, 112))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        frame = np.array(frame)
        # Normalize the pixel values to [0, 1] and convert the data type to float32
        frame = frame.astype(np.float32) / 255.0
        # Transpose the dimensions from (height, width, channels) to (channels, height, width)
        frame = np.transpose(frame, (2, 0, 1))

        # add a batch dimension
        frame = np.expand_dims(frame, axis=0)
        ort_inputs = {self.session.get_inputs()[0].name: frame}
        pre_landmark = self.session.run(None, ort_inputs)[1]
        pre_landmark = np.reshape(pre_landmark, (7, 2))
        return pre_landmark

    def draw_landmarks(self, frame: cv2.Mat, landmarks: np.ndarray) -> None:
        width, height = frame.shape[:2]
        height -= 112
        width += 112

        for point in landmarks:
            x, y = point
            cv2.circle(frame, (int(x * width), int(y * height)), 2, (0, 0, 50), -1)

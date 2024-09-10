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

Haar Surround Feature by: Summer
Algorithm App Implementation By: Prohurtz, PallasNeko, RamesTheGeneric, ShyAssassin

Copyright (c) 2024 EyeTrackVR <3
This project is licensed under the MIT License. See LICENSE for more details.
------------------------------------------------------------------------------------------------------
"""

# TODO: things we should do
# 1. Add type hints to all functions
# 2. Simplify mainloop logic?
# 3. Smoothing between blinks
# 4. Fix the very rare bug related to weird image shapes

import cv2
import numpy as np
from enum import Enum
from copy import deepcopy
from functools import lru_cache
from cv2.typing import MatLike, Point
from ..processes import EyeProcessor
from ..utils import BaseAlgorithm, safe_crop
from ..types import EyeData, TrackerPosition, TRACKING_FAILED


# cache param
lru_maxsize_vvs = 16
lru_maxsize_vs = 64
lru_maxsize_s = 128
# CV param
default_radius = 20
auto_radius_range = (default_radius - 18, default_radius + 15)  # (10,30)
auto_radius_step = 1


class CVMode(Enum):
    FIRST_FRAME = 0
    RADIUS_ADJUST = 1
    BLINK_ADJUST = 2
    NORMAL = 3


class HSF(BaseAlgorithm):
    def __init__(self, eye_processor: EyeProcessor):
        self.ep = eye_processor
        self.mode = CVMode.FIRST_FRAME
        self.center_q1 = BlinkDetector()
        self.blink_detector = BlinkDetector()
        self.auto_radius_calc = AutoRadiusCalc()
        self.center_correct = CenterCorrection()
        self.cvparam = CvParameters(default_radius, self.ep.config.hsf.default_step)

    # TODO: i would like to split this into smaller functions
    def run(self, frame: MatLike, tracker_position: TrackerPosition) -> tuple[EyeData, MatLike]:
        # adjustment of radius
        if self.mode == CVMode.RADIUS_ADJUST:
            self.cvparam.radius = self.auto_radius_calc.get_radius()
            if self.auto_radius_calc.adj_comp_flag:
                self.ep.logger.info(f"Auto Radius Complete: {self.cvparam.radius}")
                self.mode = CVMode.BLINK_ADJUST if not self.ep.config.hsf.skip_blink_detection else CVMode.NORMAL

        radius, pad, step, hsf = self.cvparam.get_rpsh()
        # Calculate the integral image of the frame
        (
            frame_pad,
            frame_int,
            inner_sum,
            in_p00,
            in_p11,
            in_p01,
            in_p10,
            y_ro_m,
            x_ro_m,
            y_ro_p,
            x_ro_p,
            outer_sum,
            out_p_temp,
            out_p00,
            out_p11,
            out_p01,
            out_p10,
            response_list,
            frame_conv,
            frame_conv_stride,
        ) = get_frameint_empty_array(frame.shape, pad, step[0], step[1], hsf.r_in, hsf.r_out)
        # BORDER_CONSTANT is faster than BORDER_REPLICATE There seems to be almost no negative impact when BORDER_CONSTANT is used.
        cv2.copyMakeBorder(frame, pad, pad, pad, pad, cv2.BORDER_CONSTANT, dst=frame_pad)
        cv2.integral(frame_pad, sum=frame_int, sdepth=cv2.CV_32S)

        # Convolve the feature with the integral image
        response, hsf_min_loc = conv_int(
            frame_int,
            hsf,
            inner_sum,
            in_p00,
            in_p11,
            in_p01,
            in_p10,
            y_ro_m,
            x_ro_m,
            y_ro_p,
            x_ro_p,
            outer_sum,
            out_p_temp,
            out_p00,
            out_p11,
            out_p01,
            out_p10,
            response_list,
            frame_conv_stride,
        )

        # Define the center point and radius
        center_x, center_y = get_hsf_center(pad, step[0], step[1], hsf_min_loc)
        upper_x = center_x + radius
        lower_x = center_x - radius
        upper_y = center_y + radius
        lower_y = center_y - radius

        # Crop the image using the calculated bounds
        cropped_image = safe_crop(frame, lower_x, lower_y, upper_x, upper_y)
        if 0 in cropped_image.shape:
            self.ep.logger.error("Cropped image has bad dimensions, skipping frame.")
            return TRACKING_FAILED, frame

        blink = 1
        match self.mode:
            case CVMode.NORMAL:
                orig_x, orig_y = deepcopy((center_x, center_y))
                if not self.blink_detector.detect(cv2.mean(cropped_image)[0]):
                    # The resolution should have changed and the statistics should have changed, so essentially the statistics
                    # need to be reworked, but implementation will be postponed as viability is the highest priority
                    if not self.center_correct.setup_comp:
                        self.center_correct.init_array(frame, self.center_q1.quartile_1)
                    elif self.center_correct.frame_shape != frame.shape:
                        self.center_correct.init_array(frame, self.center_q1.quartile_1)
                    center_x, center_y = self.center_correct.correction(frame, center_x, center_y)
                else:
                    # FIXME: since this is binary blink we should use a smoothing function to avoid flickering from false negatives
                    blink = 0

                cv2.circle(frame, (orig_x, orig_y), 6, (0, 0, 255), -1)
            case CVMode.BLINK_ADJUST:  # We dont have enough frames yet, gather more data
                if self.blink_detector.response_len() < self.ep.config.hsf.blink_stat_frames:
                    lower_x = center_x - max(20, radius)
                    lower_y = center_y - max(20, radius)
                    upper_x = center_x + max(20, radius)
                    upper_y = center_y + max(20, radius)

                    self.blink_detector.add_response(cv2.mean(cropped_image)[0])
                    self.center_q1.add_response(
                        cv2.mean(
                            safe_crop(
                                frame,
                                lower_x,
                                lower_y,
                                upper_x,
                                upper_y,
                                keepsize=False,
                            )
                        )[0]
                    )
                else:
                    self.mode = CVMode.NORMAL
                    self.center_q1.calc_thresh()
                    self.blink_detector.calc_thresh()
                    self.ep.logger.info("Blink Adjust Complete")
            case CVMode.FIRST_FRAME | CVMode.RADIUS_ADJUST:  # record current radius and response
                self.auto_radius_calc.add_response(radius, response)
            case _:
                self.ep.logger.error(f"Invalid mode: {self.mode}")
        cv2.circle(frame, (center_x, center_y), 3, (255, 0, 0), -1)

        # Moving from first_frame to the next mode
        if self.mode == CVMode.FIRST_FRAME:
            self.ep.logger.info("First frame complete")
            if self.ep.config.hsf.skip_autoradius and self.ep.config.hsf.skip_blink_detection:
                self.mode = CVMode.NORMAL
                self.ep.logger.info("Skipping autoradius and blink adjust")
            elif self.ep.config.hsf.skip_autoradius:
                self.mode = CVMode.BLINK_ADJUST
                self.ep.logger.info("Skipping autoradius")
            else:
                self.mode = CVMode.RADIUS_ADJUST
                self.ep.logger.info("Starting autoradius")

        # FIXME: this seems correct, but isnt as sensitive as it should be
        # Maybe callibration / ROI cropping plays a role in this?
        x = center_x / frame.shape[1]
        y = center_y / frame.shape[0]

        return EyeData(x, y, blink, tracker_position), frame


# If you want to update response_max. it may be more cost-effective to rewrite response_list in the following way
# https://stackoverflow.com/questions/42771110/fastest-way-to-left-cycle-a-numpy-array-like-pop-push-for-a-queue
class BlinkDetector:
    def __init__(self):
        self.quartile_1: float = 0.0
        self.response_max: float = 0.0
        self.response_list: list[float] = []

    def calc_thresh(self):
        quartile_1, quartile_3 = np.percentile(np.array(self.response_list), [25, 75])
        self.quartile_1 = quartile_1
        iqr = quartile_3 - quartile_1
        self.response_max = float(quartile_3 + (iqr * 1.5))

    def detect(self, now_response: float) -> bool:
        return now_response > self.response_max

    def add_response(self, response: float):
        self.response_list.append(response)

    def response_len(self) -> int:
        return len(self.response_list)


# What in the name of god is this?
class CvParameters:
    # It may be a little slower because a dict named "self" is read for each function call.
    def __init__(self, radius: int, step: tuple[int, int]):
        self._radius = radius
        self.pad = 2 * radius
        self._step = step
        self._hsf = HaarSurroundFeature(radius)

    def get_rpsh(self):
        return self._radius, self.pad, self._step, self._hsf
        # Essentially, the following would be preferable, but it would take twice as long to call.
        # return self.radius, self.pad, self.step, self.hsf

    @property
    def radius(self) -> int:
        return self._radius

    @radius.setter
    def radius(self, now_radius: int):
        self._radius = now_radius
        self.pad = 2 * now_radius
        self.hsf = now_radius

    @property
    def step(self) -> tuple[int, int]:
        return self._step

    @step.setter
    def step(self, now_step: tuple[int, int]):
        self._step = now_step

    @property
    def hsf(self):
        return self._hsf

    @hsf.setter
    def hsf(self, now_radius: int):
        self._hsf = HaarSurroundFeature(now_radius)


class HaarSurroundFeature:
    def __init__(self, r_inner, r_outer=None, val=None):
        if r_outer is None:
            r_outer = r_inner * 3
        r_inner2 = r_inner * r_inner
        count_inner = r_inner2
        count_outer = r_outer * r_outer - r_inner2

        if val is None:
            val_inner = 1.0 / r_inner2
            val_outer = -val_inner * count_inner / count_outer

        else:
            val_inner = val[0]
            val_outer = val[1]

        self.val_in = float(val_inner)
        self.val_out = float(val_outer)
        self.r_in = r_inner
        self.r_out = r_outer

    def get_kernel(self):
        # Defined here, but not yet used?
        # Create a kernel filled with the value of self.val_out
        kernel = np.ones(shape=(2 * self.r_out - 1, 2 * self.r_out - 1), dtype=np.float64) * self.val_out

        # Set the values of the inner area of the kernel using array slicing
        start = self.r_out - self.r_in
        end = self.r_out + self.r_in - 1
        kernel[start:end, start:end] = self.val_in

        return kernel


class AutoRadiusCalc:
    def __init__(self):
        self.response_list = []
        self.radius_cand_list = []
        self.adj_comp_flag = False

        # self.radius_middle_index = None

        # self.left_item = None
        # self.right_item = None
        # self.left_index = None
        # self.right_index = None

    def get_radius(self) -> int:
        prev_res_len = len(self.response_list)
        # adjustment of radius
        if prev_res_len == 1:
            self.adj_comp_flag = False
            return auto_radius_range[0]
        elif prev_res_len == 2:
            self.adj_comp_flag = False
            return auto_radius_range[1]
        elif prev_res_len == 3:
            if self.response_list[1][1] < self.response_list[2][1]:
                self.left_item = self.response_list[1]
                self.right_item = self.response_list[0]
            else:
                self.left_item = self.response_list[0]
                self.right_item = self.response_list[2]
            self.radius_cand_list = [
                i
                for i in range(
                    self.left_item[0],
                    self.right_item[0] + auto_radius_step,
                    auto_radius_step,
                )
            ]
            self.left_index = 0
            self.right_index: int = len(self.radius_cand_list) - 1
            self.radius_middle_index = (self.left_index + self.right_index) // 2
            self.adj_comp_flag = False
            return self.radius_cand_list[self.radius_middle_index]
        else:
            if self.left_index <= self.right_index and self.left_index != self.radius_middle_index:
                if (self.left_item[1] + self.response_list[-1][1]) < (self.right_item[1] + self.response_list[-1][1]):
                    self.right_item = self.response_list[-1]
                    self.right_index = self.radius_middle_index - 1
                    self.radius_middle_index = (self.left_index + self.right_index) // 2
                    self.adj_comp_flag = False
                    return self.radius_cand_list[self.radius_middle_index]
                if (self.left_item[1] + self.response_list[-1][1]) > (self.right_item[1] + self.response_list[-1][1]):
                    self.left_item = self.response_list[-1]
                    self.left_index = self.radius_middle_index + 1
                    self.radius_middle_index = (self.left_index + self.right_index) // 2
                    self.adj_comp_flag = False
                    return self.radius_cand_list[self.radius_middle_index]
            self.adj_comp_flag = True
            return self.radius_cand_list[self.radius_middle_index]

    def get_radius_base(self) -> int:
        """
        Use it when the new version doesn't work well.
        :return:
        """

        prev_res_len = len(self.response_list)
        # adjustment of radius
        if prev_res_len == 1:
            self.adj_comp_flag = False
            return auto_radius_range[0]
        elif prev_res_len == 2:
            self.adj_comp_flag = False
            return auto_radius_range[1]
        elif prev_res_len == 3:
            sort_res = sorted(self.response_list, key=lambda x: x[1])[0]
            # Extract the radius with the lowest response value
            if sort_res[0] == default_radius:
                # If the default value is best, change now_mode to init after setting radius to the default value.
                self.adj_comp_flag = True
                return default_radius
            elif sort_res[0] == auto_radius_range[0]:
                self.radius_cand_list = [i for i in range(auto_radius_range[0], default_radius, auto_radius_step)][1:]
                self.adj_comp_flag = False
                return self.radius_cand_list.pop()
            else:
                self.radius_cand_list = [i for i in range(default_radius, auto_radius_range[1], auto_radius_step)][1:]
                self.adj_comp_flag = False
                return self.radius_cand_list.pop()
        else:
            # Try the contents of the radius_cand_list in order until the radius_cand_list runs out
            # Better make it a binary search.
            if len(self.radius_cand_list) == 0:
                sort_res = sorted(self.response_list, key=lambda x: x[1])[0]
                self.adj_comp_flag = True
                return sort_res[0]
            else:
                self.adj_comp_flag = False
                return self.radius_cand_list.pop()

    def add_response(self, radius, response):
        self.response_list.append((radius, response))


class CenterCorrection:
    def __init__(self):
        # Tunable parameters
        kernel_size = 7  # 3 or 5 or 7
        self.hist_thr = float(4)  # 4%
        self.center_q1_radius = 20

        self.setup_comp = False
        # self.quartile_1 = None
        # self.frame_shape = None
        # self.frame_mask = None
        # self.frame_bin = None
        # self.frame_final = None
        self.morph_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
        self.morph_kernel2 = np.ones((3, 3))
        self.hist_index = np.arange(256)
        self.hist = np.empty((256, 1))
        self.hist_norm = np.empty((256, 1))

    def init_array(self, frame: MatLike, quartile_1):
        self.frame_shape = frame.shape
        self.frame_mask = np.empty(frame.shape, dtype=np.uint8)
        self.frame_bin = np.empty(frame.shape, dtype=np.uint8)
        self.frame_final: np.ndarray = np.empty(frame.shape, dtype=np.uint8)
        self.quartile_1 = quartile_1
        self.setup_comp = True

    def correction(self, frame: MatLike, orig_x: int, orig_y: int) -> tuple[int, int]:
        center_x, center_y = orig_x, orig_y
        self.frame_mask.fill(0)

        # bottleneck
        cv2.calcHist([frame], [0], None, [256], [0, 256], hist=self.hist)

        cv2.normalize(self.hist, self.hist_norm, alpha=100.0, norm_type=cv2.NORM_L1)
        hist_per = self.hist_norm.cumsum()
        hist_index_list = self.hist_index[hist_per >= self.hist_thr]
        bitwise: np.ndarray = cv2.bitwise_or(255 - self.frame_mask, frame)
        frame_thr = float(hist_index_list[0] if len(hist_index_list) else np.percentile(bitwise, 4))

        # bottleneck
        self.frame_bin = cv2.threshold(frame, frame_thr, 1, cv2.THRESH_BINARY_INV)[1]  # type: ignore[assignment]
        cropped_x, cropped_y, cropped_w, cropped_h = cv2.boundingRect(self.frame_bin)

        self.frame_final = cv2.bitwise_and(self.frame_bin, self.frame_mask)

        # bottleneck
        self.frame_finalcv: np.ndarray = cv2.morphologyEx(self.frame_final, cv2.MORPH_CLOSE, self.morph_kernel)
        self.frame_final = cv2.morphologyEx(self.frame_final, cv2.MORPH_OPEN, self.morph_kernel)

        if not self.frame_shape == (cropped_h, cropped_w):
            base_x = cropped_x + cropped_w // 2
            base_y = cropped_y + cropped_h // 2
            if self.frame_final[base_y, base_x] != 1:
                if self.frame_final[center_y, center_x] != 1:
                    self.frame_final = np.ndarray(
                        cv2.morphologyEx(
                            self.frame_final,
                            cv2.MORPH_DILATE,
                            self.morph_kernel2,
                            iterations=3,
                        ),  # type: ignore[reportArgumentType]
                        dtype=np.uint8,
                    )
                else:
                    base_x, base_y = center_x, center_y
        else:
            # Not detected.
            base_x, base_y = center_x, center_y

        contours, _ = cv2.findContours(self.frame_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contours_box = [cv2.boundingRect(cnt) for cnt in contours]
        contours_dist = np.array(
            [abs(base_x - (cnt_x + cnt_w / 2)) + abs(base_y - (cnt_y + cnt_h / 2)) for cnt_x, cnt_y, cnt_w, cnt_h in contours_box]
        )

        if len(contours_box):
            cropped_x2, cropped_y2, cropped_w2, cropped_h2 = contours_box[contours_dist.argmin()]
            x = cropped_x2 + cropped_w2 // 2
            y = cropped_y2 + cropped_h2 // 2
        else:
            x = center_x
            y = center_y

        out_x, out_y = orig_x, orig_y

        if (
            frame[
                int(max(y - 5, 0)) : int(min(y + 5, self.frame_shape[0])),
                int(max(x - 5, 0)) : int(min(x + 5, self.frame_shape[1])),
            ].min()
            < self.quartile_1
        ):
            out_x = x
            out_y = y
        return out_x, out_y


@lru_cache(maxsize=lru_maxsize_vvs)
def get_frameint_empty_array(frame_shape, pad, x_step, y_step, r_in, r_out):
    frame_int_dtype = np.intc
    frame_pad = np.empty((frame_shape[0] + (pad * 2), frame_shape[1] + (pad * 2)), dtype=np.uint8)

    row, col = frame_pad.shape

    frame_int = np.empty((row + 1, col + 1), dtype=frame_int_dtype)

    y_steps_arr = np.arange(pad, row - pad, y_step, dtype=np.int16)
    x_steps_arr = np.arange(pad, col - pad, x_step, dtype=np.int16)
    len_sx, len_sy = len(x_steps_arr), len(y_steps_arr)
    len_syx = (len_sy, len_sx)
    y_end = pad + (y_step * (len_sy - 1))
    x_end = pad + (x_step * (len_sx - 1))

    y_rin_m = slice(pad - r_in, y_end - r_in + 1, y_step)
    y_rin_p = slice(pad + r_in, y_end + r_in + 1, y_step)
    x_rin_m = slice(pad - r_in, x_end - r_in + 1, x_step)
    x_rin_p = slice(pad + r_in, x_end + r_in + 1, x_step)

    in_p00 = frame_int[y_rin_m, x_rin_m]
    in_p11 = frame_int[y_rin_p, x_rin_p]
    in_p01 = frame_int[y_rin_m, x_rin_p]
    in_p10 = frame_int[y_rin_p, x_rin_m]

    y_ro_m = np.maximum(y_steps_arr - r_out, 0)  # [:,np.newaxis]
    x_ro_m = np.maximum(x_steps_arr - r_out, 0)  # [np.newaxis,:]
    y_ro_p = np.minimum(row, y_steps_arr + r_out)  # [:,np.newaxis]
    x_ro_p = np.minimum(col, x_steps_arr + r_out)  # [np.newaxis,:]

    inner_sum = np.empty(len_syx, dtype=frame_int_dtype)
    outer_sum = np.empty(len_syx, dtype=frame_int_dtype)

    out_p_temp = np.empty((len_sy, col + 1), dtype=frame_int_dtype)
    out_p00 = np.empty(len_syx, dtype=frame_int_dtype)
    out_p11 = np.empty(len_syx, dtype=frame_int_dtype)
    out_p01 = np.empty(len_syx, dtype=frame_int_dtype)
    out_p10 = np.empty(len_syx, dtype=frame_int_dtype)
    response_list = np.empty(len_syx, dtype=np.float64)  # or np.int32
    frame_conv = np.zeros(shape=(row - 2 * pad, col - 2 * pad), dtype=np.uint8)  # or np.float64
    frame_conv_stride = frame_conv[::y_step, ::x_step]

    return (
        frame_pad,
        frame_int,
        inner_sum,
        in_p00,
        in_p11,
        in_p01,
        in_p10,
        y_ro_m,
        x_ro_m,
        y_ro_p,
        x_ro_p,
        outer_sum,
        out_p_temp,
        out_p00,
        out_p11,
        out_p01,
        out_p10,
        response_list,
        frame_conv,
        frame_conv_stride,
    )


def conv_int(
    frame_int,
    kernel,
    inner_sum,
    in_p00,
    in_p11,
    in_p01,
    in_p10,
    y_ro_m,
    x_ro_m,
    y_ro_p,
    x_ro_p,
    outer_sum,
    out_p_temp,
    out_p00,
    out_p11,
    out_p01,
    out_p10,
    response_list,
    frame_conv_stride,
) -> tuple[float, Point]:
    # inner_sum[:, :] = in_p00 + in_p11 - in_p01 - in_p10
    cv2.add(in_p00, in_p11, dst=inner_sum)
    cv2.subtract(inner_sum, in_p01, dst=inner_sum)
    cv2.subtract(inner_sum, in_p10, dst=inner_sum)

    # p00 calc
    frame_int.take(y_ro_m, axis=0, mode="clip", out=out_p_temp)
    out_p_temp.take(x_ro_m, axis=1, mode="clip", out=out_p00)
    # p01 calc
    out_p_temp.take(x_ro_p, axis=1, mode="clip", out=out_p01)
    # p11 calc
    frame_int.take(y_ro_p, axis=0, mode="clip", out=out_p_temp)
    out_p_temp.take(x_ro_p, axis=1, mode="clip", out=out_p11)
    # p10 calc
    out_p_temp.take(x_ro_m, axis=1, mode="clip", out=out_p10)

    # outer_sum[:, :] = out_p00 + out_p11 - out_p01 - out_p10 - inner_sum
    cv2.add(out_p00, out_p11, dst=outer_sum)
    cv2.subtract(outer_sum, out_p01, dst=outer_sum)
    cv2.subtract(outer_sum, out_p10, dst=outer_sum)
    cv2.subtract(outer_sum, inner_sum, dst=outer_sum)
    cv2.addWeighted(
        inner_sum,
        kernel.val_in,
        outer_sum,  # or p00 + p11 - p01 - p10 - inner_sum
        kernel.val_out,
        0.0,
        dtype=cv2.CV_64F,  # or cv2.CV_32S
        dst=response_list,
    )

    min_response, _, min_loc, _ = cv2.minMaxLoc(response_list)

    frame_conv_stride[:, :] = response_list

    return min_response, min_loc


@lru_cache(maxsize=lru_maxsize_s)
def get_hsf_center(padding, x_step, y_step, min_loc) -> tuple[int, int]:
    return (
        padding + (x_step * min_loc[0]) - padding,
        padding + (y_step * min_loc[1]) - padding,
    )

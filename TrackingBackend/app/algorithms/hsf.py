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

Haar Surround Feature: Summer, PallasNeko (Optimization)
Algorithm App Implementations and tweaks By: Prohurtz, RamesTheGeneric

Copyright (c) 2023 EyeTrackVR <3
------------------------------------------------------------------------------------------------------
"""

from app.processes import EyeProcessor
from app.utils import BaseAlgorithm
from cv2.typing import MatLike
from app.types import EyeData
import timeit
from functools import lru_cache
import cv2
import numpy as np
from enum import IntEnum
import psutil
import sys
import os

class HSF(BaseAlgorithm):
    def __init__(self, eye_processor: EyeProcessor):
        self.ep = eye_processor
        self.er = External_Run_HSF()

    def run(self, frame: MatLike) -> EyeData:
        center_x, center_y, frame, radius = self.er.run(frame)
        center_x = center_x/255     # Find better way to transform this output unless
        center_y = center_y/255     # minmax calibration takes care of it as a raw value.
        blink = 0                   # Does hsf have a blink method?
        return EyeData(center_x, center_y, blink, self.ep.tracker_position)


skip_autoradius = False
skip_blink_detect = False
# cache param
lru_maxsize_vvs = 16
lru_maxsize_vs = 64
lru_maxsize_s = 128
# CV param
default_radius = 20
auto_radius_range = (default_radius - 18, default_radius + 15)  # (10,30)
auto_radius_step = 1
blink_init_frames = 60 * 3  # 60fps*3sec,Number of blink statistical frames
# step==(x,y)
default_step = (
    5,
    5,
)  # bigger the steps,lower the processing time! ofc acc also takes an impact


def safe_crop(frame: MatLike, x, y, x2, y2, keepsize=False):    # Couldn't import this from utils :shrug:
    try:
        # The order of the arguments can be reconsidered.
        frame_h, frame_w = frame.shape[:2]
        outframe = frame[max(0, y) : min(frame_h, y2), max(0, x) : min(frame_w, x2)].copy()
        reqsize_x, reqsize_y = abs(x2 - x), abs(y2 - y)
        if keepsize and outframe.shape[:2] != (reqsize_y, reqsize_x):
            # If the size is different from the expected size (smaller by the amount that is out of range)
            outframe = cv2.resize(outframe, (reqsize_x, reqsize_y))
        return outframe
    except cv2.error as e:
        if '!ssize.empty()' in str(e):
            print("Image is None or has zero dimensions. Skipping resizing.")
        else:
            raise

class CvParameters:
    # It may be a little slower because a dict named "self" is read for each function call.
    def __init__(self, radius, step):
        self._radius = radius
        self.pad = 2 * radius
        self._step = step
        self._hsf = HaarSurroundFeature(radius)

    def get_rpsh(self):
        return self._radius, self.pad, self._step, self._hsf
        # Essentially, the following would be preferable, but it would take twice as long to call.
        # return self.radius, self.pad, self.step, self.hsf

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, now_radius):
        self._radius = now_radius
        self.pad = 2 * now_radius
        self.hsf = now_radius

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, now_step):
        self._step = now_step

    @property
    def hsf(self):
        return self._hsf

    @hsf.setter
    def hsf(self, now_radius):
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
        kernel = (
            np.ones(shape=(2 * self.r_out - 1, 2 * self.r_out - 1), dtype=np.float64)
            * self.val_out
        )

        # Set the values of the inner area of the kernel using array slicing
        start = self.r_out - self.r_in
        end = self.r_out + self.r_in - 1
        kernel[start:end, start:end] = self.val_in

        return kernel


def to_gray(frame):
    # Faster by quitting checking if the input image is already grayscale
    # Perhaps it would be faster with less overhead to call cv2.cvtColor directly instead of using this function
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


@lru_cache(maxsize=lru_maxsize_vvs)
def get_frameint_empty_array(frame_shape, pad, x_step, y_step, r_in, r_out):
    frame_int_dtype = np.intc
    frame_pad = np.empty(
        (frame_shape[0] + (pad * 2), frame_shape[1] + (pad * 2)), dtype=np.uint8
    )

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
    frame_conv = np.zeros(
        shape=(row - 2 * pad, col - 2 * pad), dtype=np.uint8
    )  # or np.float64
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
):
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
def get_hsf_center(padding, x_step, y_step, min_loc):  # min_x,min_y):
    return (
        padding + (x_step * min_loc[0]) - padding,
        padding + (y_step * min_loc[1]) - padding,
    )


class AutoRadiusCalc(object):
    def __init__(self):
        self.response_list = []
        self.radius_cand_list = []
        self.adj_comp_flag = False

        self.radius_middle_index = None

        self.left_item = None
        self.right_item = None
        self.left_index = None
        self.right_index = None

    def get_radius(self):
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
            self.right_index = len(self.radius_cand_list) - 1
            self.radius_middle_index = (self.left_index + self.right_index) // 2
            self.adj_comp_flag = False
            return self.radius_cand_list[self.radius_middle_index]
        else:
            if (
                self.left_index <= self.right_index
                and self.left_index != self.radius_middle_index
            ):
                if (self.left_item[1] + self.response_list[-1][1]) < (
                    self.right_item[1] + self.response_list[-1][1]
                ):
                    self.right_item = self.response_list[-1]
                    self.right_index = self.radius_middle_index - 1
                    self.radius_middle_index = (self.left_index + self.right_index) // 2
                    self.adj_comp_flag = False
                    return self.radius_cand_list[self.radius_middle_index]
                if (self.left_item[1] + self.response_list[-1][1]) > (
                    self.right_item[1] + self.response_list[-1][1]
                ):
                    self.left_item = self.response_list[-1]
                    self.left_index = self.radius_middle_index + 1
                    self.radius_middle_index = (self.left_index + self.right_index) // 2
                    self.adj_comp_flag = False
                    return self.radius_cand_list[self.radius_middle_index]
            self.adj_comp_flag = True
            return self.radius_cand_list[self.radius_middle_index]

    def get_radius_base(self):
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
                self.radius_cand_list = [
                    i
                    for i in range(
                        auto_radius_range[0], default_radius, auto_radius_step
                    )
                ][1:]
                self.adj_comp_flag = False
                return self.radius_cand_list.pop()
            else:
                self.radius_cand_list = [
                    i
                    for i in range(
                        default_radius, auto_radius_range[1], auto_radius_step
                    )
                ][1:]
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
        return None


class BlinkDetector(object):
    def __init__(self):
        self.response_list = []
        self.response_max = None
        self.enable_detect_flg = False
        self.quartile_1 = None

    def calc_thresh(self):
        quartile_1, quartile_3 = np.percentile(np.array(self.response_list), [25, 75])
        self.quartile_1 = quartile_1
        iqr = quartile_3 - quartile_1
        self.response_max = float(quartile_3 + (iqr * 1.5))

        self.enable_detect_flg = True
        return None

    def detect(self, now_response):
        return now_response > self.response_max

    def add_response(self, response):
        self.response_list.append(response)
        return None

    def response_len(self):
        return len(self.response_list)


class CenterCorrection(object):
    def __init__(self):
        # Tunable parameters
        kernel_size = 7  # 3 or 5 or 7
        self.hist_thr = float(4)  # 4%
        self.center_q1_radius = 20

        self.setup_comp = False
        self.quartile_1 = None
        self.radius = None
        self.frame_shape = None
        self.frame_mask = None
        self.frame_bin = None
        self.frame_final = None
        self.morph_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (kernel_size, kernel_size)
        )
        self.morph_kernel2 = np.ones((3, 3))
        self.hist_index = np.arange(256)
        self.hist = np.empty((256, 1))
        self.hist_norm = np.empty((256, 1))

    def init_array(self, gray_shape, quartile_1, radius):
        self.frame_shape = gray_shape
        self.frame_mask = np.empty(gray_shape, dtype=np.uint8)
        self.frame_bin = np.empty(gray_shape, dtype=np.uint8)
        self.frame_final = np.empty(gray_shape, dtype=np.uint8)
        self.quartile_1 = quartile_1
        self.radius = radius
        self.setup_comp = True

    def correction(self, gray_frame, orig_x, orig_y):
        center_x, center_y = orig_x, orig_y
        self.frame_mask.fill(0)

        # bottleneck
        cv2.calcHist([gray_frame], [0], None, [256], [0, 256], hist=self.hist)

        cv2.normalize(self.hist, self.hist_norm, alpha=100.0, norm_type=cv2.NORM_L1)
        hist_per = self.hist_norm.cumsum()
        hist_index_list = self.hist_index[hist_per >= self.hist_thr]
        frame_thr = (
            hist_index_list[0]
            if len(hist_index_list)
            else np.percentile(cv2.bitwise_or(255 - self.frame_mask, gray_frame), 4)
        )

        # bottleneck
        self.frame_bin = cv2.threshold(gray_frame, frame_thr, 1, cv2.THRESH_BINARY_INV)[
            1
        ]
        cropped_x, cropped_y, cropped_w, cropped_h = cv2.boundingRect(self.frame_bin)

        self.frame_final = cv2.bitwise_and(self.frame_bin, self.frame_mask)

        # bottleneck
        self.frame_final = cv2.morphologyEx(
            self.frame_final, cv2.MORPH_CLOSE, self.morph_kernel
        )
        self.frame_final = cv2.morphologyEx(
            self.frame_final, cv2.MORPH_OPEN, self.morph_kernel
        )

        if (cropped_h, cropped_w) == self.frame_shape:
            # Not detected.
            base_x, base_y = center_x, center_y
        else:
            base_x = cropped_x + cropped_w // 2
            base_y = cropped_y + cropped_h // 2
            if self.frame_final[base_y, base_x] != 1:
                if self.frame_final[center_y, center_x] != 1:
                    self.frame_final = cv2.morphologyEx(
                        self.frame_final,
                        cv2.MORPH_DILATE,
                        self.morph_kernel2,
                        iterations=3,
                    )
                else:
                    base_x, base_y = center_x, center_y

        contours, _ = cv2.findContours(
            self.frame_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )
        contours_box = [cv2.boundingRect(cnt) for cnt in contours]
        contours_dist = np.array(
            [
                abs(base_x - (cnt_x + cnt_w / 2)) + abs(base_y - (cnt_y + cnt_h / 2))
                for cnt_x, cnt_y, cnt_w, cnt_h in contours_box
            ]
        )

        if len(contours_box):
            cropped_x2, cropped_y2, cropped_w2, cropped_h2 = contours_box[
                contours_dist.argmin()
            ]
            x = cropped_x2 + cropped_w2 // 2
            y = cropped_y2 + cropped_h2 // 2
        else:
            x = center_x
            y = center_y

        out_x, out_y = orig_x, orig_y

        if (
            gray_frame[
                int(max(y - 5, 0)) : int(min(y + 5, self.frame_shape[0])),
                int(max(x - 5, 0)) : int(min(x + 5, self.frame_shape[1])),
            ].min()
            < self.quartile_1
        ):
            out_x = x
            out_y = y
        return out_x, out_y


class HSF_cls(object):
    def __init__(self):
        # I'd like to take into account things like print, end_time - start_time processing time, etc., but it's too much trouble.

        # For measuring total processing time

        self.main_start_time = timeit.default_timer()

        self.rng = np.random.default_rng()
        self.cvparam = CvParameters(default_radius, default_step)

        self.cv_modeo = ["first_frame", "radius_adjust", "blink_adjust", "normal"]
        self.now_modeo = self.cv_modeo[0]

        self.auto_radius_calc = AutoRadiusCalc()
        self.blink_detector = BlinkDetector()
        self.center_q1 = BlinkDetector()
        self.center_correct = CenterCorrection()

        self.cap = None

        self.timedict = {
            "to_gray": [],
            "int_img": [],
            "conv_int": [],
            "crop": [],
            "total_cv": [],
        }
    cct = 300
    ransac_lower_x = 100
    ransac_lower_y = 100
    cx = 0
    cy = 0

    def single_run(self):
        frame = self.current_image_gray
        if self.now_modeo == self.cv_modeo[1]:
            # adjustment of radius
            self.cvparam.radius = self.auto_radius_calc.get_radius()
            if self.auto_radius_calc.adj_comp_flag:
                self.now_modeo = (
                    self.cv_modeo[2] if not skip_blink_detect else self.cv_modeo[3]
                )

        radius, pad, step, hsf = self.cvparam.get_rpsh()

        # For measuring processing time of image processing
        cv_start_time = timeit.default_timer()

        gray_frame = frame
        self.timedict["to_gray"].append(timeit.default_timer() - cv_start_time)

        # Calculate the integral image of the frame
        int_start_time = timeit.default_timer()
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
        ) = get_frameint_empty_array(
            gray_frame.shape, pad, step[0], step[1], hsf.r_in, hsf.r_out
        )
        # BORDER_CONSTANT is faster than BORDER_REPLICATE There seems to be almost no negative impact when BORDER_CONSTANT is used.
        cv2.copyMakeBorder(
            gray_frame, pad, pad, pad, pad, cv2.BORDER_CONSTANT, dst=frame_pad
        )
        cv2.integral(frame_pad, sum=frame_int, sdepth=cv2.CV_32S)
        self.timedict["int_img"].append(timeit.default_timer() - int_start_time)

        # Convolve the feature with the integral image
        conv_int_start_time = timeit.default_timer()
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
        center_xy = get_hsf_center(pad, step[0], step[1], hsf_min_loc)

        self.timedict["conv_int"].append(timeit.default_timer() - conv_int_start_time)

        crop_start_time = timeit.default_timer()
        # Define the center point and radius
        center_x, center_y = center_xy
        upper_x = center_x + radius
        lower_x = center_x - radius
        upper_y = center_y + radius
        lower_y = center_y - radius

        # Crop the image using the calculated bounds

        cropped_image = safe_crop(gray_frame, lower_x, lower_y, upper_x, upper_y)
        if self.now_modeo == self.cv_modeo[0] or self.now_modeo == self.cv_modeo[1]:
            # If mode is first_frame or radius_adjust, record current radius and response
            self.auto_radius_calc.add_response(radius, response)
        elif self.now_modeo == self.cv_modeo[2]:
            # Statistics for blink detection
            pass
            
            if self.blink_detector.response_len() < blink_init_frames:
                self.blink_detector.add_response(cv2.mean(cropped_image)[0])

                upper_x = center_x + max(
                    20, radius
                )  # self.center_correct.center_q1_radius
                lower_x = center_x - max(
                    20, radius
                )  # self.center_correct.center_q1_radius
                upper_y = center_y + max(
                    20, radius
                )  # self.center_correct.center_q1_radius
                lower_y = center_y - max(
                    20, radius
                )  # self.center_correct.center_q1_radius

                self.center_q1.add_response(
                    cv2.mean(
                        safe_crop(
                            gray_frame,
                            lower_x,
                            lower_y,
                            upper_x,
                            upper_y,
                            keepsize=False,
                        )
                    )[0]
                )

            else:

                self.blink_detector.calc_thresh()
                self.center_q1.calc_thresh()
                self.now_modeo = self.cv_modeo[3]
            
        else:
            if 0 in cropped_image.shape:
                # If shape contains 0, it is not detected well.
                print("Something's wrong.")
            else:
                orig_x, orig_y = center_x, center_y
                if self.blink_detector.enable_detect_flg:
                    # If the average value of cropped_image is greater than response_max
                    # (i.e., if the cropimage is whitish
                    if self.blink_detector.detect(cv2.mean(cropped_image)[0]):
                        # blink
                        pass
                    else:
                        # pass
                        if not self.center_correct.setup_comp:
                            self.center_correct.init_array(
                                gray_frame.shape, self.center_q1.quartile_1, radius
                            )
                        elif self.center_correct.frame_shape != gray_frame.shape:
                            """The resolution should have changed and the statistics should have changed, so essentially the statistics
                            need to be reworked, but implementation will be postponed as viability is the highest priority."""
                            self.center_correct.init_array(
                                gray_frame.shape, self.center_q1.quartile_1, radius
                            )

                        center_x, center_y = self.center_correct.correction(
                            gray_frame, center_x, center_y
                        )
                        # Define the center point and radius
                        center_xy = (center_x, center_y)
                        upper_x = center_x + radius
                        lower_x = center_x - radius
                        upper_y = center_y + radius
                        lower_y = center_y - radius
                        # Crop the image using the calculated bounds
                        cropped_image = safe_crop(
                            gray_frame, lower_x, lower_y, upper_x, upper_y
                        )
                # if imshow_enable or save_video:
                cv2.circle(frame, (orig_x, orig_y), 6, (0, 0, 255), -1)
                cv2.circle(frame, (center_x, center_y), 3, (255, 0, 0), -1)

        # If you want to update response_max. it may be more cost-effective to rewrite response_list in the following way
        # https://stackoverflow.com/questions/42771110/fastest-way-to-left-cycle-a-numpy-array-like-pop-push-for-a-queue

        cv_end_time = timeit.default_timer()
        self.timedict["crop"].append(cv_end_time - crop_start_time)
        self.timedict["total_cv"].append(cv_end_time - cv_start_time)
        
        if self.now_modeo == self.cv_modeo[0]:
            # Moving from first_frame to the next mode
            if skip_autoradius and skip_blink_detect:
                self.now_modeo = self.cv_modeo[3]
            elif skip_autoradius:
                self.now_modeo = self.cv_modeo[2]
            else:
                self.now_modeo = self.cv_modeo[1]
        return center_x, center_y, frame, radius
    

class External_Run_HSF(object):
    def __init__(self, skip_autoradius_flg=False, radius=20):
        # temporary code
        global skip_autoradius, default_radius
        skip_autoradius = skip_autoradius_flg
        if skip_autoradius:
            default_radius = radius

        self.algo = HSF_cls()

    def run(self, current_image_gray):
        self.algo.current_image_gray = current_image_gray
        center_x, center_y, frame, radius = self.algo.single_run()
        return center_x, center_y, frame, radius

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

Adaptive Haar Surround Feature by: Summer, PallasNeko
Algorithm App Implementation By: Prohurtz, ShyAssassin

Copyright (c) 2024 EyeTrackVR <3
This project is licensed under the MIT License. See LICENSE for more details.
------------------------------------------------------------------------------------------------------
"""

import cv2
import numpy as np
from cv2.typing import MatLike
from functools import lru_cache
from app.utils import BaseAlgorithm
from app.processes import EyeProcessor
from app.types import EyeData, TrackerPosition, TRACKING_FAILED

# cache param
lru_maxsize_vvs = 16
lru_maxsize_vs = 64
lru_maxsize_s = 128


class AHSF(BaseAlgorithm):
    def __init__(self, eye_processor: EyeProcessor):
        self.ep = eye_processor

    def draw_coarse(self, frame, pupil_rect, outer_rect, center_fitting):
        cv2.rectangle(
            frame,
            (pupil_rect[0], pupil_rect[1]),
            (pupil_rect[0] + pupil_rect[2], pupil_rect[1] + pupil_rect[3]),
            (0, 0, 0),
            1,
        )
        cv2.rectangle(
            frame,
            (outer_rect[0], outer_rect[1]),
            (outer_rect[0] + outer_rect[2], outer_rect[1] + outer_rect[3]),
            (105, 105, 105),
            1,
        )
        cv2.drawMarker(frame, center_fitting, (255, 255, 255), cv2.MARKER_CROSS, 15, 1)

    def run(self, frame: MatLike, tracker_position: TrackerPosition) -> tuple[EyeData, MatLike]:
        average_color = np.mean(frame)
        # Get the dimensions of the rotated image
        height, width = frame.shape
        # Determine the size of the square background (choose the larger dimension)
        max_dimension = max(height, width)
        # Create a square background with the average color
        square_background = np.full((max_dimension, max_dimension), average_color, dtype=np.uint8)
        # Calculate the position to paste the rotated image onto the square background
        x_offset = (max_dimension - width) // 2
        y_offset = (max_dimension - height) // 2

        # Paste the rotated image onto the square background
        square_background[y_offset : y_offset + height, x_offset : x_offset + width] = frame
        frame = square_background

        # TODO: replace params with a dataclass
        params = {  # these can be tuned more
            "ratio_downsample": 0.5,
            "use_init_rect": False,
            "mu_outer": 250,  # aprroximatly how much pupil should be in the outer rect
            "mu_inner": 50,  # aprroximatly how much pupil should be in the inner rect
            "ratio_outer": 1.0,  # rectangular ratio. 1 means square (LIKE REGULAR HSF)
            "kf": 2,  # noise filter. May lose tracking if too high (or even never start)
            "width_min": frame.shape[1] * 0.08,  # Minimum width of the pupil
            "width_max": frame.shape[1] * 0.5,  # Maximum width of the pupil
            "wh_step": 5,  # Pupil width and height step search size
            "xy_step": 10,  # Kernel movement step search size
            "roi": (0, 0, frame.shape[1], frame.shape[0]),
            "init_rect_flag": False,
            "init_rect": (0, 0, frame.shape[1], frame.shape[0]),
        }
        try:
            (
                pupil_rect_coarse,
                outer_rect_coarse,
                max_response_coarse,
                mu_inner,
                mu_outer,
            ) = coarse_detection(frame, params)
            ellipse_rect, center_fitting = fine_detection(frame, pupil_rect_coarse)
        except TypeError:
            return TRACKING_FAILED, frame

        # x = outer_rect_coarse[0] + outer_rect_coarse[2] / 2
        # y = outer_rect_coarse[1] + outer_rect_coarse[3] / 2
        x = center_fitting[0]
        y = center_fitting[1]
        self.draw_coarse(frame, pupil_rect_coarse, outer_rect_coarse, center_fitting)

        x = x / frame.shape[1]
        y = y / frame.shape[0]

        return EyeData(x, y, 1, tracker_position), frame


@lru_cache(maxsize=lru_maxsize_vvs)
def get_empty_array(frame_shape, width_min, width_max, wh_step, xy_step, roi, ratio_outer):
    frame_int_dtype = np.intc
    np_index_dtype = (
        np.intc
    )  # memo: Better to use np.intp, but a little slower ref: https://numpy.org/doc/1.25/user/basics.indexing.html#detailed-notes

    row, col = frame_shape

    frame_int = np.empty((row + 1, col + 1), dtype=frame_int_dtype)

    w_arr = np.arange(width_min, width_max + 1, wh_step, dtype=np_index_dtype)
    h_arr = (w_arr / ratio_outer).astype(np.int16)

    # memo: It is not smart code and needs to be changed.
    y_out_n = np.hstack([np.arange(roi[1] + h, roi[3] - h, xy_step, dtype=np_index_dtype) for h in h_arr])
    x_out_n = np.hstack([np.arange(roi[0] + w, roi[2] - w, xy_step, dtype=np_index_dtype) for w in w_arr])
    y_out_h = np.hstack([np.arange(roi[1] + h, roi[3] - h, xy_step, dtype=np_index_dtype) + h for h in h_arr])
    x_out_w = np.hstack([np.arange(roi[0] + w, roi[2] - w, xy_step, dtype=np_index_dtype) + w for w in w_arr])
    out_h = y_out_h - y_out_n
    out_w = x_out_w - x_out_n

    y_in_n = np.hstack([np.arange(roi[1] + h, roi[3] - h, xy_step, dtype=np_index_dtype) + int(h / 4) for h in h_arr])
    x_in_n = np.hstack([np.arange(roi[0] + w, roi[2] - w, xy_step, dtype=np_index_dtype) + int(w / 4) for w in w_arr])
    y_in_h = np.hstack([np.arange(roi[1] + h, roi[3] - h, xy_step, dtype=np_index_dtype) + int(h / 4) + int(h / 2) for h in h_arr])
    x_in_w = np.hstack([np.arange(roi[0] + w, roi[2] - w, xy_step, dtype=np_index_dtype) + int(w / 4) + int(w / 2) for w in w_arr])
    in_h = y_in_h - y_in_n
    in_w = x_in_w - x_in_n

    wh_in_arr = (
        np.hstack(
            [
                np.full(
                    ((roi[2] - w) - (roi[0] + w) - 1) // xy_step + 1,
                    int(w / 2),
                    dtype=np_index_dtype,
                )
                for w in w_arr
            ]
        )[:, np.newaxis]
        * np.hstack(
            [
                np.full(
                    ((roi[3] - h) - (roi[1] + h) - 1) // xy_step + 1,
                    int(h / 2),
                    dtype=np_index_dtype,
                )
                for h in h_arr
            ]
        )[np.newaxis, :]
    )
    wh_out_arr = (
        np.hstack(
            [
                np.full(
                    ((roi[2] - w) - (roi[0] + w) - 1) // xy_step + 1,
                    w,
                    dtype=np_index_dtype,
                )
                for w in w_arr
            ]
        )[:, np.newaxis]
        * np.hstack(
            [
                np.full(
                    ((roi[3] - h) - (roi[1] + h) - 1) // xy_step + 1,
                    h,
                    dtype=np_index_dtype,
                )
                for h in h_arr
            ]
        )[np.newaxis, :]
    )

    mu_outer_rect = cv2.subtract(wh_out_arr, wh_in_arr)  # ,dst=) # == (outer_rect[2] * outer_rect[3] - inner_rect[2] * inner_rect[3])

    wh_in_arr = 1 / wh_in_arr  # .astype(np.float32)
    # wh_out_arr=wh_out_arr.astype(np.float64)
    mu_outer_rect = 1 / mu_outer_rect  # .astype(np.float32)
    mu_outer_rect2 = -1.0 * mu_outer_rect  # cv2.merge([mu_outer_rect,-1.0*mu_outer_rect])

    # 1/wh_in_arr == wh_in_arr_mul
    return (
        frame_int,
        y_out_n,
        x_out_n,
        y_out_h,
        x_out_w,
        out_h,
        out_w,
        y_in_n,
        x_in_n,
        y_in_h,
        x_in_w,
        in_h,
        in_w,
        wh_in_arr,
        wh_out_arr,
        mu_outer_rect,
        mu_outer_rect2,
    )


def coarse_detection(img_gray, params):
    ratio_outer = params["ratio_outer"]
    kf = params["kf"]
    width_min = params["width_min"]
    width_max = params["width_max"]
    wh_step = params["wh_step"]
    xy_step = params["xy_step"]
    roi = params["roi"]
    init_rect_flag = params["init_rect_flag"]
    init_rect = params["init_rect"]
    mu_inner = params["mu_inner"]
    mu_outer = params["mu_outer"]
    max_response_coarse = -255

    imgboundary = (0, 0, img_gray.shape[1], img_gray.shape[0])
    img_blur = np.copy(img_gray)

    # Assign values to avoid unassigned errors
    pupil_rect_coarse = (10, 10, 10, 10)
    outer_rect_coarse = (5, 5, 5, 5)

    if init_rect_flag:
        init_rect_down = rect_scale(init_rect, params["ratio_downsample"], False)
        init_rect_down = intersect_rect(init_rect_down, imgboundary)
        img_blur = img_gray[
            init_rect_down[1] : init_rect_down[1] + init_rect_down[3],
            init_rect_down[0] : init_rect_down[0] + init_rect_down[2],
        ]

    (
        frame_int,
        y_out_n,
        x_out_n,
        y_out_h,
        x_out_w,
        out_h,
        out_w,
        y_in_n,
        x_in_n,
        y_in_h,
        x_in_w,
        in_h,
        in_w,
        wh_in_arr,
        wh_out_arr,
        mu_outer_rect,
        mu_outer_rect2,
    ) = get_empty_array(img_blur.shape, width_min, width_max, wh_step, xy_step, roi, ratio_outer)
    cv2.integral(
        img_blur, sum=frame_int, sdepth=cv2.CV_32S
    )  # memo: It becomes slower when using float64, probably because the increase in bits from 32 to 64 causes the arrays to be larger

    # memo: If axis=1 is too slow, just transpose and "take" with axis=0.
    # memo: This URL gave me an idea.  https://numpy.org/doc/1.25/dev/internals.html#multidimensional-array-indexing-order-issues
    out_p_temp = frame_int.take(y_out_n, axis=0, mode="clip")  # , out=out_p_temp)
    out_p_temp = cv2.transpose(out_p_temp)
    out_p00 = out_p_temp.take(x_out_n, axis=0, mode="clip")  # , out=out_p00)
    # p01 calc
    out_p01 = out_p_temp.take(x_out_w, axis=0, mode="clip")  # , out=out_p01)
    # p11 calc
    out_p_temp = frame_int.take(y_out_h, axis=0, mode="clip")  # , out=out_p_temp)
    out_p_temp = cv2.transpose(out_p_temp)
    out_p11 = out_p_temp.take(x_out_w, axis=0, mode="clip")  # , out=out_p11)
    # p10 calc
    out_p10 = out_p_temp.take(x_out_n, axis=0, mode="clip")  # , out=out_p10)

    # outer_sum[:, :] = out_p00 + out_p11 - out_p01 - out_p10
    outer_sum = cv2.add(out_p00, out_p11)  # , dst=outer_sum)
    cv2.subtract(outer_sum, out_p01, dst=outer_sum)
    cv2.subtract(outer_sum, out_p10, dst=outer_sum)

    in_p_temp = frame_int.take(y_in_n, axis=0, mode="clip")  # , out=in_p_temp)

    in_p_temp = cv2.transpose(in_p_temp)
    in_p00 = in_p_temp.take(x_in_n, axis=0, mode="clip")  # , out=in_p00)
    # p01 calc
    in_p01 = in_p_temp.take(x_in_w, axis=0, mode="clip")  # , out=in_p01)
    # p11 calc
    in_p_temp = frame_int.take(y_in_h, axis=0, mode="clip")  # , out=in_p_temp)
    in_p_temp = cv2.transpose(in_p_temp)
    in_p11 = in_p_temp.take(x_in_w, axis=0, mode="clip")  # , out=in_p11)
    # p10 calc
    in_p10 = in_p_temp.take(x_in_n, axis=0, mode="clip")  # , out=in_p10)

    inner_sum = cv2.add(in_p00, in_p11)
    cv2.subtract(inner_sum, in_p01, dst=inner_sum)
    cv2.subtract(inner_sum, in_p10, dst=inner_sum)

    # memo: Multiplication, etc. can be faster by self-assignment, but care must be taken because array initialization is required.
    # https://stackoverflow.com/questions/71204415/opencv-python-fastest-way-to-multiply-pixel-value
    inner_sum_f = np.empty(inner_sum.shape, dtype=np.float64)
    inner_sum_f[:, :] = inner_sum
    outer_sum_f = np.empty(outer_sum.shape, dtype=np.float64)
    outer_sum_f[:, :] = outer_sum

    response_value = np.empty(outer_sum.shape, dtype=np.float64)
    inout_rect_sum = mu_outer_rect2.copy()
    inout_rect_mul = mu_outer_rect.copy()

    cv2.multiply(inner_sum_f, inout_rect_mul, inout_rect_mul)
    cv2.multiply(outer_sum_f, inout_rect_sum, inout_rect_sum)
    cv2.add(inout_rect_mul, inout_rect_sum, dst=inout_rect_sum)

    cv2.multiply(inner_sum_f, wh_in_arr, inner_sum_f, kf)
    cv2.add(inout_rect_sum, inner_sum_f, dst=response_value)

    # memo: The input image is transposed, so the coordinate output of this function has x and y swapped.
    min_response, max_response, min_loc, max_loc = cv2.minMaxLoc(response_value)

    # The sign is reversed from the original calculation result, so using min.
    rec_o = (
        x_out_n[min_loc[1]],
        y_out_n[min_loc[0]],
        out_w[min_loc[1]],
        out_h[min_loc[0]],
    )
    rec_in = (
        x_in_n[min_loc[1]],
        y_in_n[min_loc[0]],
        in_w[min_loc[1]],
        in_h[min_loc[0]],
    )
    max_response_coarse = -min_response
    pupil_rect_coarse = rec_in
    outer_rect_coarse = rec_o

    return pupil_rect_coarse, outer_rect_coarse, max_response_coarse, mu_inner, mu_outer


def fine_detection(frame, pupil_rect_coarse):
    valid_ratio = 1.2
    boundary = (0, 0, frame.shape[1], frame.shape[0])
    valid_rect = intersect_rect(rect_scale(pupil_rect_coarse, valid_ratio), boundary)
    img_pupil = frame[
        valid_rect[1] : valid_rect[1] + valid_rect[3],
        valid_rect[0] : valid_rect[0] + valid_rect[2],
    ]
    img_pupil_blur = cv2.GaussianBlur(img_pupil, (5, 5), 0, 0)
    edges_filter = detect_edges(img_pupil_blur)
    # fit ellipse to edges
    contours, hierarchy = cv2.findContours(edges_filter, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # sort contours by area
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
    # fit ellipse to largest contour
    try:
        if len(contours) > 0 and len(contours[0]) >= 5:
            pupil_contour = contours[0]
            pupil_ellipse = cv2.fitEllipse(pupil_contour)
            center_fitting = (
                int(pupil_ellipse[0][0] + valid_rect[0]),
                int(pupil_ellipse[0][1] + valid_rect[1]),
            )
            pupil_rect_fine = (
                int(pupil_ellipse[0][0] - pupil_ellipse[1][0] / 2),
                int(pupil_ellipse[0][1] - pupil_ellipse[1][1] / 2),
                int(pupil_ellipse[1][0]),
                int(pupil_ellipse[1][1]),
            )
            pupil_rect_fine = (
                pupil_rect_fine[0] + valid_rect[0],
                pupil_rect_fine[1] + valid_rect[1],
                pupil_rect_fine[2],
                pupil_rect_fine[3],
            )
            pupil_rect_fine = intersect_rect(pupil_rect_fine, boundary)
            pupil_rect_fine = rect_scale(pupil_rect_fine, 1 / valid_ratio)
        else:
            pupil_rect_fine = pupil_rect_coarse
            center_fitting = (
                int(pupil_rect_fine[0] + pupil_rect_fine[2] / 2),
                int(pupil_rect_fine[1] + pupil_rect_fine[3] / 2),
            )
        return pupil_rect_fine, center_fitting
    except Exception:
        center = (pupil_rect_coarse[0] + pupil_rect_coarse[2] / 2, pupil_rect_coarse[1] + pupil_rect_coarse[3] / 2)
        return pupil_rect_coarse, center


def detect_edges(img_pupil_blur):
    edges = cv2.Canny(img_pupil_blur, 64, 128)

    # img_bw = np.zeros_like(img_pupil_blur)
    # img_bw[img_pupil_blur > 100] = 255
    img_bw = cv2.compare(img_pupil_blur, 100, cv2.CMP_GT)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    img_bw = cv2.dilate(img_bw, kernel)

    # edges_filter = edges & (~img_bw)
    # or
    edges_filter = cv2.bitwise_and(edges, cv2.bitwise_not(img_bw))
    return edges_filter


def rect_scale(rect, scale, round_up=True):
    x, y, width, height = rect
    new_width = int(width * scale)
    new_height = int(height * scale)
    if round_up:
        new_width = int(np.ceil(width * scale))
        new_height = int(np.ceil(height * scale))
    new_x = x + int((width - new_width) / 2)
    new_y = y + int((height - new_height) / 2)
    return new_x, new_y, new_width, new_height


def intersect_rect(rect1, rect2):
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    x = max(x1, x2)
    y = max(y1, y2)
    w = min(x1 + w1, x2 + w2) - x
    h = min(y1 + h1, y2 + h2) - y
    return x, y, w, h

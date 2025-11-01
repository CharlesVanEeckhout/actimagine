import numpy as np
import logging

from ..frame_includes import *
from .common import *

logger = logging.getLogger(__name__)
logger.propagate = True # enable/disable


class KeyframeOnlySimple:
    def __init__(self):
        self.vframe = None
        self.writer = None
        self.goal_plane_buffers = None
        self.coeff_buffers = None
        self.dct_filters = None


    def coeff_buffer_getter(self, plane, x, y):
        step = get_step(plane)
        return self.coeff_buffers[plane][y // (step * 4) + 1][x // (step * 4) + 1]


    def coeff_buffer_setter(self, plane, x, y, value):
        step = get_step(plane)
        self.coeff_buffers[plane][y // (step * 4) + 1][x // (step * 4) + 1] = value


    def predict_dc(self, block, plane):
        dc = 128
        logger.debug("predict_dc")
        logger.debug(block)
        if block["x"] != 0 and block["y"] != 0:
            # average of both averages below
            sum_x = block["w"] // 2
            for x in range(block["w"]):
                sum_x += self.vframe.plane_buffer_getter(plane, block["x"]+x, block["y"]-1)

            sum_y = block["h"] // 2
            for y in range(block["h"]):
                sum_y += self.vframe.plane_buffer_getter(plane, block["x"]-1, block["y"]+y)

            dc = ((sum_x // block["w"]) + (sum_y // block["h"]) + 1) // 2

        elif block["x"] == 0 and block["y"] != 0:
            # average of pixels on the top border of current block
            sum_x = block["w"] // 2
            for x in range(block["w"]):
                sum_x += self.vframe.plane_buffer_getter(plane, block["x"]+x, block["y"]-1)

            dc = sum_x // block["w"]

        elif block["x"] != 0 and block["y"] == 0:
            # average of pixels on the left border of current block
            sum_y = block["h"] // 2
            for y in range(block["h"]):
                sum_y += self.vframe.plane_buffer_getter(plane, block["x"]-1, block["y"]+y)

            dc = sum_y // block["h"]
        logger.debug(dc)
        def predict_dc_callback(x, y, plane):
            self.vframe.plane_buffer_setter(plane, x, y, dc)

        plane_buffer_iterator(block, plane, predict_dc_callback)


    def predict_notile(self, block):
        self.writer.unsigned_expgolomb(2) # predict_dc
        self.predict_dc(block, "y")

        self.predict_notile_uv(block)


    def predict_notile_uv(self, block):
        self.writer.unsigned_expgolomb(0) # predict_dc
        self.predict_dc(block, "u")
        self.predict_dc(block, "v")


    def encode_mb(self, block):
        if block["w"] > block["h"]:
            # split the block in left and right parts
            self.writer.unsigned_expgolomb(0)
            self.encode_mb(block_half_left(block))
            self.encode_mb(block_half_right(block))
            if block["w"] == 8 and block["h"] >= 8:
                self.clear_total_coeff(block)
            return

        if block["h"] > 8:
            # split the block in up and down parts
            self.writer.unsigned_expgolomb(2)
            self.encode_mb(block_half_up(block))
            self.encode_mb(block_half_down(block))
            if block["w"] >= 8 and block["h"] == 8:
                self.clear_total_coeff(block)
            return

        # blocks are 8x8 here
        self.writer.unsigned_expgolomb(22) # predict notile, residu
        self.predict_notile(block)
        encode_residu_blocks(self, block)


    def encode(self, frame_encoder):
        self.vframe = frame_encoder.vframe
        self.writer = frame_encoder.writer
        self.goal_plane_buffers = frame_encoder.goal_plane_buffers

        self.coeff_buffers = {
            "y": np.zeros((self.vframe.height // 4 + 1, self.vframe.width // 4 + 1), dtype=np.uint16),
            "uv": np.zeros((self.vframe.height // 8 + 1, self.vframe.width // 8 + 1), dtype=np.uint16)
        }

        self.dct_filters = get_dct_filters(self.vframe.qtab)

        for y in range(0, self.vframe.height, 16):
            for x in range(0, self.vframe.width, 16):
                block = {
                    "x": x,
                    "y": y,
                    "w": 16,
                    "h": 16
                }

                self.encode_mb(block)

        # align with word
        while self.writer.bit_number != 15:
            self.writer.bit(0)

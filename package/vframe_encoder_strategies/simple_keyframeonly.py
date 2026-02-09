import numpy as np
import logging

from ..frame_includes import *
from .vframe_encoder_strategy_abstract import VFrameEncoderStrategyAbstract
from .common import *

logger = logging.getLogger(__name__)
logger.propagate = True # enable/disable


class SimpleKeyframeOnly(VFrameEncoderStrategyAbstract):
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
        self.predict_dc(block, "y")
        self.predict_dc(block, "u")
        self.predict_dc(block, "v")
        residu_cr = encode_residu_blocks_check(self, block)
        if residu_cr["is_worth_encoding"]:
            self.writer.unsigned_expgolomb(22) # predict notile, residu
            self.writer.unsigned_expgolomb(2) # predict_notile.predict_dc
            self.writer.unsigned_expgolomb(0) # predict_notile_uv.predict_dc
            encode_residu_blocks_write(self, residu_cr)
        else:
            self.writer.unsigned_expgolomb(11) # predict notile, no residu
            self.writer.unsigned_expgolomb(2) # predict_notile.predict_dc
            self.writer.unsigned_expgolomb(0) # predict_notile_uv.predict_dc


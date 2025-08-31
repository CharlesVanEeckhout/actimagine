import numpy as np
import logging

from .. import vlc
from ..frame_includes import *

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


    def encode_residu_blocks(self, block):
        # residu block is 8x8 px which contains 4 4x4 px blocks for y and 1 double-size 4x4 px block for uv
        # since blocks here are 8x8 px, they will have 1 residu block
        residu_mask = 0x1F
        residu_mask_tab_index = ff_actimagine_vx_residu_mask_new_tab.index(residu_mask)
        self.writer.unsigned_expgolomb(residu_mask_tab_index)

        coeff_left = self.coeff_buffer_getter("y", block["x"]  -1, block["y"]    )
        coeff_top  = self.coeff_buffer_getter("y", block["x"]    , block["y"]  -1)
        nc = int((coeff_left + coeff_top + 1) // 2)
        out_total_coeff = self.encode_residu_cavlc(block["x"]  , block["y"]  , nc, "y")
        self.coeff_buffer_setter("y", block["x"]  , block["y"]  , out_total_coeff)

        coeff_left = self.coeff_buffer_getter("y", block["x"]+4-1, block["y"]    )
        coeff_top  = self.coeff_buffer_getter("y", block["x"]+4  , block["y"]  -1)
        nc = int((coeff_left + coeff_top + 1) // 2)
        out_total_coeff = self.encode_residu_cavlc(block["x"]+4, block["y"]  , nc, "y")
        self.coeff_buffer_setter("y", block["x"]+4, block["y"]  , out_total_coeff)

        coeff_left = self.coeff_buffer_getter("y", block["x"]  -1, block["y"]+4  )
        coeff_top  = self.coeff_buffer_getter("y", block["x"]    , block["y"]+4-1)
        nc = int((coeff_left + coeff_top + 1) // 2)
        out_total_coeff = self.encode_residu_cavlc(block["x"]  , block["y"]+4, nc, "y")
        self.coeff_buffer_setter("y", block["x"]  , block["y"]+4, out_total_coeff)

        coeff_left = self.coeff_buffer_getter("y", block["x"]+4-1, block["y"]+4  )
        coeff_top  = self.coeff_buffer_getter("y", block["x"]+4  , block["y"]+4-1)
        nc = int((coeff_left + coeff_top + 1) // 2)
        out_total_coeff = self.encode_residu_cavlc(block["x"]+4, block["y"]+4, nc, "y")
        self.coeff_buffer_setter("y", block["x"]+4, block["y"]+4, out_total_coeff)

        coeff_left = self.coeff_buffer_getter("uv", block["x"]-1, block["y"]  )
        coeff_top  = self.coeff_buffer_getter("uv", block["x"]  , block["y"]-1)
        nc = int((coeff_left + coeff_top + 1) // 2)
        out_total_coeff_u = self.encode_residu_cavlc(block["x"], block["y"], nc, "u")
        out_total_coeff_v = self.encode_residu_cavlc(block["x"], block["y"], nc, "v")
        out_total_coeff = int((out_total_coeff_u + out_total_coeff_v + 1) // 2)
        self.coeff_buffer_setter("uv", block["x"], block["y"], out_total_coeff)


    def encode_residu_cavlc(self, x, y, nc, plane):
        level = self.encode_dct(x, y, plane)

        # apply level to actual_plane_buffers
        self.decode_dct(x, y, plane, level)

        # prepare level to be encoded

        # trailing zeros
        for i in range(len(level)-1, -1, -1):
            if level[i] != 0:
                break
            level.pop(i)

        logger.debug(level)

        if len(level) == 0:
            # encode empty residu
            trailing_ones = 0
            total_coeff   = 0
            coeff_token = (total_coeff << 2) + trailing_ones
            self.writer.vlc2(coeff_token, vlc.coeff_token_vlc[ff_h264_cavlc_coeff_token_table_index[nc]])
            return total_coeff

        # zeros run before
        run_before_zeros = []
        run_before_current_zero = 0
        zeros_left = 0 # TotalZeros
        for i in range(len(level)-2, -1, -1):
            if level[i] == 0:
                run_before_current_zero += 1
                zeros_left += 1
                level.pop(i)
            else:
                run_before_zeros.append(run_before_current_zero)
                run_before_current_zero = 0

        logger.debug("run_before_zeros: " + str(run_before_zeros))
        logger.debug("zeros_left: " + str(zeros_left))
        logger.debug(level)

        # trailing one coefficients
        total_coeff = len(level)
        trailing_ones_signbits = []
        for i in range(len(level)-1, 0, -1): # even if the leftmost coeff is 1, it cannot be a trailing one
            if abs(level[i]) == 1:
                # signbit of 1 is 0 and signbit of -1 is 1
                trailing_ones_signbits.append(1 if level[i] < 0 else 0)

                level.pop(i)
                if len(trailing_ones_signbits) == 3:
                    break
            else:
                break
        trailing_ones = len(trailing_ones_signbits)
        coeff_token = (total_coeff << 2) + trailing_ones
        logger.debug("trailing_ones: " + str(trailing_ones))
        logger.debug(level)

        # non trailing one coefficients
        suffix_length = 0
        level_code_signbits = []
        level_prefixes = []
        level_suffixes = []
        real_suffix_lengths = []
        for i in range(len(level)-1, -1, -1):
            level_code = level[i]
            level_code_signbits.append(1 if level[i] < 0 else 0)
            level[i] = abs(level[i]) - 1
            level_prefix = min(level[i] >> suffix_length, 15)
            level_suffix = level[i] - (level_prefix << suffix_length)
            real_suffix_length = 11 if level_prefix == 15 else suffix_length
            if level_suffix >= (1 << real_suffix_length):
                raise RuntimeError("level_suffix too large")
            level_prefixes.append(level_prefix)
            level_suffixes.append(level_suffix)
            real_suffix_lengths.append(real_suffix_length)

            logger.debug("level_code " + str(level_code) + " vs suffix limit "+ str(ff_h264_cavlc_suffix_limit[suffix_length + 1]))
            suffix_length += 1 if abs(level_code) > ff_h264_cavlc_suffix_limit[suffix_length + 1] else 0

            level.pop(i)

        logger.debug("level_code_signbits: " + str(level_code_signbits))
        logger.debug("level_prefixes:      " + str(level_prefixes))
        logger.debug("level_suffixes:      " + str(level_suffixes))
        logger.debug("real_suffix_lengths: " + str(real_suffix_lengths))

        # encode level

        self.writer.vlc2(coeff_token, vlc.coeff_token_vlc[ff_h264_cavlc_coeff_token_table_index[nc]])
        if total_coeff != 16:
            self.writer.vlc2(zeros_left, vlc.total_zeros_vlc[total_coeff])

        while True:
            if len(trailing_ones_signbits) > 0:
                trailing_ones_signbit = trailing_ones_signbits.pop(0)
                self.writer.bit(trailing_ones_signbit)
            else:
                level_prefix = level_prefixes.pop(0)
                level_suffix = level_suffixes.pop(0)
                real_suffix_length = real_suffix_lengths.pop(0)
                level_code_signbit = level_code_signbits.pop(0)

                for i in range(level_prefix):
                    self.writer.bit(0)
                self.writer.bit(1)

                self.writer.int_to_bits(level_suffix, real_suffix_length)

                self.writer.bit(level_code_signbit)

            if len(level_code_signbits) == 0:
                break

            if zeros_left == 0:
                continue

            run_before = run_before_zeros.pop(0)

            logger.debug("zeros_left: " + str(zeros_left))
            logger.debug("run_before: " + str(run_before))
            if zeros_left < 7:
                self.writer.vlc2(run_before, vlc.run_vlc[zeros_left])
            else:
                self.writer.vlc2(run_before, vlc.run7_vlc)

            zeros_left -= run_before
        return total_coeff


    def encode_dct(self, x, y, plane):
        step = 1 if plane == "y" else 2
        goal_residu = []
        for yy in range(y//step, y//step+4):
            row = []
            for xx in range(x//step, x//step+4):
                row.append(
                    int(self.goal_plane_buffers[plane][yy][xx]) -
                    int(self.vframe.plane_buffers[plane][yy][xx])
                )
            logger.debug(row)
            goal_residu.append(row)

        # average of goal_residu times filter
        averages = []
        for dct_filter in self.dct_filters:
            average = 0
            for yy in range(4):
                for xx in range(4):
                    average += goal_residu[yy][xx] * dct_filter[yy][xx]
            average /= 16
            averages.append(average)

        level = []
        for i in range(16):
            level.append(round(averages[zigzag_scan[i]]))
        logger.debug(level)
        return level


    def decode_dct(self, x, y, plane, level):
        dct = [None] * len(zigzag_scan)

        # dezigzag
        for i, z in enumerate(zigzag_scan):
            dct[z] = level[i]

        # dequantize
        for i in range(16):
            dct[i] *= self.vframe.qtab[(i & 1) + ((i >> 2) & 1)]

        # h264_idct_add
        step = 1 if plane == "y" else 2

        dct[0] += 1 << 5

        for i in range(4):
            z0 =  dct[i + 4*0]     +  dct[i + 4*2]
            z1 =  dct[i + 4*0]     -  dct[i + 4*2]
            z2 = (dct[i + 4*1]//2) -  dct[i + 4*3]
            z3 =  dct[i + 4*1]     + (dct[i + 4*3]//2)

            dct[i + 4*0] = z0 + z3
            dct[i + 4*1] = z1 + z2
            dct[i + 4*2] = z1 - z2
            dct[i + 4*3] = z0 - z3

        for i in range(4):
            z0 =  dct[0 + 4*i]     +  dct[2 + 4*i]
            z1 =  dct[0 + 4*i]     -  dct[2 + 4*i]
            z2 = (dct[1 + 4*i]//2) -  dct[3 + 4*i]
            z3 =  dct[1 + 4*i]     + (dct[3 + 4*i]//2)

            p = av_clip_pixel(self.vframe.plane_buffer_getter(plane, x+step*i, y+step*0) + ((z0 + z3) >> 6))
            self.vframe.plane_buffer_setter(plane, x+step*i, y+step*0, p)
            p = av_clip_pixel(self.vframe.plane_buffer_getter(plane, x+step*i, y+step*1) + ((z1 + z2) >> 6))
            self.vframe.plane_buffer_setter(plane, x+step*i, y+step*1, p)
            p = av_clip_pixel(self.vframe.plane_buffer_getter(plane, x+step*i, y+step*2) + ((z1 - z2) >> 6))
            self.vframe.plane_buffer_setter(plane, x+step*i, y+step*2, p)
            p = av_clip_pixel(self.vframe.plane_buffer_getter(plane, x+step*i, y+step*3) + ((z0 - z3) >> 6))
            self.vframe.plane_buffer_setter(plane, x+step*i, y+step*3, p)


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
        self.encode_residu_blocks(block)


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

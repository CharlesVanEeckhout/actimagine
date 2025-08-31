import numpy as np
import logging

from . import vlc
from . import h264pred
from .frame_includes import *

logger = logging.getLogger(__name__)
logger.propagate = True # enable/disable


class VFrameDecoder:
    def __init__(self, vframe, reader):
        self.vframe = vframe
        self.reader = reader
        self.coeff_buffers = None
        self.vectors = None


    def coeff_buffer_getter(self, plane, x, y):
        step = get_step(plane)
        return self.coeff_buffers[plane][y // (step * 4) + 1][x // (step * 4) + 1]


    def coeff_buffer_setter(self, plane, x, y, value):
        step = get_step(plane)
        self.coeff_buffers[plane][y // (step * 4) + 1][x // (step * 4) + 1] = value


    def predict_inter(self, block, pred_vec, has_delta, ref_vframe):
        if ref_vframe is None:
            raise RuntimeError("ref_vframe was None")

        vec = pred_vec.copy()
        if has_delta:
            vec["x"] += self.reader.signed_expgolomb()
            vec["y"] += self.reader.signed_expgolomb()

        if block["x"] + vec["x"] < 0 or block["x"] + vec["x"] + block["w"] > self.vframe.width or \
            block["y"] + vec["y"] < 0 or block["y"] + vec["y"] + block["h"] > self.vframe.height:
            raise RuntimeError("motion vector moves block out of bounds")

        self.vectors[(block["y"] // 16) + 1][(block["x"] // 16) + 1] = vec

        def predict_inter_callback(x, y, plane):
            self.vframe.plane_buffer_setter(plane, x, y,
                ref_vframe.plane_buffer_getter(plane, x+vec["x"], y+vec["y"])
            )

        plane_buffer_iterator(block, "yuv", predict_inter_callback)


    def predict_inter_dc(self, block):
        vec = {
            "x": self.reader.signed_expgolomb(),
            "y": self.reader.signed_expgolomb()
        }

        if block["x"] + vec["x"] < 0 or block["x"] + vec["x"] + block["w"] > self.vframe.width or \
            block["y"] + vec["y"] < 0 or block["y"] + vec["y"] + block["h"] > self.vframe.height:
            raise RuntimeError("motion vector out of bounds")

        dc = {}
        dc["y"] = self.reader.signed_expgolomb()
        if dc["y"] < -(1 << 16) or dc["y"] >= (1 << 16):
            raise RuntimeError("invalid dc offset")
        dc["y"] *= 2

        dc["u"] = self.reader.signed_expgolomb()
        if dc["u"] < -(1 << 16) or dc["u"] >= (1 << 16):
            raise RuntimeError("invalid dc offset")
        dc["u"] *= 2

        dc["v"] = self.reader.signed_expgolomb()
        if dc["v"] < -(1 << 16) or dc["v"] >= (1 << 16):
            raise RuntimeError("invalid dc offset")
        dc["v"] *= 2

        def predict_inter_dc_callback(x, y, plane):
            self.vframe.plane_buffer_setter(plane, x, y,
                av_clip_pixel(self.vframe.ref_vframes[0].plane_buffer_getter(plane, x+vec["x"], y+vec["y"]) + dc[plane])
            )

        plane_buffer_iterator(block, "yuv", predict_inter_dc_callback)


    def predict_notile(self, block):
        mode = self.reader.unsigned_expgolomb()
        logger.debug("predict notile " + str(mode))
        if mode == 0:
            self.predict_vertical(block, "y")
        elif mode == 1:
            self.predict_horizontal(block, "y")
        elif mode == 2:
            self.predict_dc(block, "y")
        elif mode == 3:
            self.predict_plane(block, "y", 0)
        else:
            raise RuntimeError("invalid predict notile mode " + str(mode))
        self.predict_notile_uv(block)


    def predict_notile_uv(self, block):
        mode = self.reader.unsigned_expgolomb()
        logger.debug("predict notile uv " + str(mode))
        if mode == 0:
            self.predict_dc(block, "u")
            self.predict_dc(block, "v")
        elif mode == 1:
            self.predict_horizontal(block, "u")
            self.predict_horizontal(block, "v")
        elif mode == 2:
            self.predict_vertical(block, "u")
            self.predict_vertical(block, "v")
        elif mode == 3:
            self.predict_plane(block, "u", 0)
            self.predict_plane(block, "v", 0)
        else:
            raise RuntimeError("invalid predict notile uv mode " + str(mode))


    def predict4(self, block):
        pred4_cache = []
        for i in range(5):
            pred4_cache.append([])
            for j in range(5):
                pred4_cache[i].append(9)

        for y2 in range(block["h"] // 4):
            for x2 in range(block["w"] // 4):
                mode = min(pred4_cache[1 + y2 - 1][1 + x2], pred4_cache[1 + y2][1 + x2 - 1])
                if mode == 9:
                    mode = 2

                if self.reader.bit() == 0:
                    val = self.reader.int_from_bits(3)
                    mode = val + (val >= mode)*1

                pred4_cache[1 + y2][1 + x2] = mode

                dst = {
                    "x": block["x"] + x2*4,
                    "y": block["y"] + y2*4
                }

                if mode == 0: # vertical
                    h264pred.pred4x4_vertical(self.vframe.plane_buffers["y"], dst)
                elif mode == 1: # horizontal
                    h264pred.pred4x4_horizontal(self.vframe.plane_buffers["y"], dst)
                elif mode == 2: # dc
                    if dst["x"] == 0 and dst["y"] == 0:
                        h264pred.pred4x4_128_dc(self.vframe.plane_buffers["y"], dst)
                    elif dst["x"] == 0 and dst["y"] != 0:
                        h264pred.pred4x4_top_dc(self.vframe.plane_buffers["y"], dst)
                    elif dst["x"] != 0 and dst["y"] == 0:
                        h264pred.pred4x4_left_dc(self.vframe.plane_buffers["y"], dst)
                    else:
                        h264pred.pred4x4_dc(self.vframe.plane_buffers["y"], dst)
                elif mode == 3: # diagonal-down-left
                    h264pred.pred4x4_down_left(self.vframe.plane_buffers["y"], dst)
                elif mode == 4: # diagonal-down-right
                    h264pred.pred4x4_down_right(self.vframe.plane_buffers["y"], dst)
                elif mode == 5: # vertical-right
                    h264pred.pred4x4_vertical_right(self.vframe.plane_buffers["y"], dst)
                elif mode == 6: # horizontal-down
                    h264pred.pred4x4_horizontal_down(self.vframe.plane_buffers["y"], dst)
                elif mode == 7: # vertical-left
                    h264pred.pred4x4_vertical_left(self.vframe.plane_buffers["y"], dst)
                elif mode == 8: # horizontal-up
                    h264pred.pred4x4_horizontal_up(self.vframe.plane_buffers["y"], dst)
                else:
                    raise RuntimeError("invalid predict4 mode " + str(mode))

        self.predict_notile_uv(block)


    def predict_dc(self, block, plane):
        dc = 128
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

        def predict_dc_callback(x, y, plane):
            self.vframe.plane_buffer_setter(plane, x, y, dc)

        plane_buffer_iterator(block, plane, predict_dc_callback)


    def predict_horizontal(self, block, plane):
        def predict_horizontal_callback(x, y, plane):
            # get pixel from the left border of current block
            pixel = self.vframe.plane_buffer_getter(plane, block["x"]-1, y)
            self.vframe.plane_buffer_setter(plane, x, y, pixel)

        plane_buffer_iterator(block, plane, predict_horizontal_callback)


    def predict_vertical(self, block, plane):
        def predict_vertical_callback(x, y, plane):
            # get pixel from the top border of current block
            pixel = self.vframe.plane_buffer_getter(plane, x, block["y"]-1)
            self.vframe.plane_buffer_setter(plane, x, y, pixel)

        plane_buffer_iterator(block, plane, predict_vertical_callback)


    def predict_plane(self, block, plane, param):
        bottom_left = self.vframe.plane_buffer_getter(plane, block["x"]-1, block["y"]+block["h"]-1)
        top_right = self.vframe.plane_buffer_getter(plane, block["x"]+block["w"]-1, block["y"]-1)
        logger.debug("plane bottom_left: " + str(bottom_left))
        logger.debug("plane top_right: " + str(top_right))
        logger.debug("plane param: " + str(param))
        pixel = (bottom_left + top_right + 1) // 2 + param
        logger.debug("plane px: " + str(pixel))
        self.vframe.plane_buffer_setter(plane, block["x"]+block["w"]-1, block["y"]+block["h"]-1, pixel)

        def predict_plane_intern(block, plane):
            step = get_step(plane)

            if block["w"] == step and block["h"] == step:
                return
            elif block["w"] == step and block["h"] > step:
                top = self.vframe.plane_buffer_getter(plane, block["x"], block["y"]-1)
                bottom = self.vframe.plane_buffer_getter(plane, block["x"], block["y"]+block["h"]-1)
                pixel = (top + bottom) // 2
                self.vframe.plane_buffer_setter(plane, block["x"], block["y"]+(block["h"]//2)-1, pixel)
                predict_plane_intern(block_half_up(block), plane)
                predict_plane_intern(block_half_down(block), plane)
            elif block["w"] > step and block["h"] == step:
                left = self.vframe.plane_buffer_getter(plane, block["x"]-1, block["y"])
                right = self.vframe.plane_buffer_getter(plane, block["x"]+block["w"]-1, block["y"])
                pixel = (left + right) // 2
                self.vframe.plane_buffer_setter(plane, block["x"]+(block["w"]//2)-1, block["y"], pixel)
                predict_plane_intern(block_half_left(block), plane)
                predict_plane_intern(block_half_right(block), plane)
            else:
                bottom_left = self.vframe.plane_buffer_getter(plane, block["x"]-1, block["y"]+block["h"]-1)
                top_right = self.vframe.plane_buffer_getter(plane, block["x"]+block["w"]-1, block["y"]-1)
                bottom_right = self.vframe.plane_buffer_getter(plane, block["x"]+block["w"]-1, block["y"]+block["h"]-1)
                bottom_center = (bottom_left + bottom_right) // 2
                center_right = (top_right + bottom_right) // 2
                self.vframe.plane_buffer_setter(plane, block["x"]+(block["w"]//2)-1, block["y"]+block["h"]-1, bottom_center)
                self.vframe.plane_buffer_setter(plane, block["x"]+block["w"]-1, block["y"]+(block["h"]//2)-1, center_right)
                if (block["w"] == 4*step or block["w"] == 16*step) is not (block["h"] == 4*step or block["h"] == 16*step):
                    center_left = self.vframe.plane_buffer_getter(plane, block["x"]-1, block["y"]+(block["h"]//2)-1)
                    pixel = (center_left + center_right) // 2
                else:
                    top_center = self.vframe.plane_buffer_getter(plane, block["x"]+(block["w"]//2)-1, block["y"]-1)
                    pixel = (top_center + bottom_center) // 2
                self.vframe.plane_buffer_setter(plane, block["x"]+(block["w"]//2)-1, block["y"]+(block["h"]//2)-1, pixel)
                predict_plane_intern(block_half_up(block_half_left(block)), plane)
                predict_plane_intern(block_half_up(block_half_right(block)), plane)
                predict_plane_intern(block_half_down(block_half_left(block)), plane)
                predict_plane_intern(block_half_down(block_half_right(block)), plane)

        predict_plane_intern(block, plane)


    def predict_mb_plane(self, block):
        # y
        param = self.reader.signed_expgolomb()
        if param < -(1 << 16) or param >= (1 << 16):
            raise RuntimeError("invalid plane param " + str(param))
        logger.debug("mbplane y param: " + str(param))
        self.predict_plane(block, "y", param * 2)

        # u
        param = self.reader.signed_expgolomb()
        if param < -(1 << 16) or param >= (1 << 16):
            raise RuntimeError("invalid plane param " + str(param))
        logger.debug("mbplane u param: " + str(param))
        self.predict_plane(block, "u", param * 2)

        # v
        param = self.reader.signed_expgolomb()
        if param < -(1 << 16) or param >= (1 << 16):
            raise RuntimeError("invalid plane param " + str(param))
        logger.debug("mbplane v param: " + str(param))
        self.predict_plane(block, "v", param * 2)


    def decode_residu_blocks(self, block):
        # residu block is 8x8 px which contains 4 4x4 px blocks for y and 1 8x8 px block for uv
        for y in range(0, block["h"], 8):
            for x in range(0, block["w"], 8):
                residu_mask_tab_index = self.reader.unsigned_expgolomb()
                if residu_mask_tab_index > 0x1F:
                    raise RuntimeError("invalid residu mask tab index " + str(residu_mask_tab_index))
                residu_mask = ff_actimagine_vx_residu_mask_new_tab[residu_mask_tab_index]
                logger.debug("residu block (" + str(x) + ", " + str(y) + ") mask " + "{:05b}".format(residu_mask))

                if residu_mask & 1 != 0:
                    coeff_left = self.coeff_buffer_getter("y", block["x"]+x  -1, block["y"]+y    )
                    coeff_top  = self.coeff_buffer_getter("y", block["x"]+x    , block["y"]+y  -1)
                    nc = int((coeff_left + coeff_top + 1) // 2)
                    out_total_coeff = self.decode_residu_cavlc(block["x"]+x  , block["y"]+y  , nc, "y")
                    logger.debug("out_total_coeff bit0: " + str(out_total_coeff))
                    self.coeff_buffer_setter("y", block["x"]+x  , block["y"]+y  , out_total_coeff)
                else:
                    self.coeff_buffer_setter("y", block["x"]+x  , block["y"]+y  , 0)

                if residu_mask & 2 != 0:
                    coeff_left = self.coeff_buffer_getter("y", block["x"]+x+4-1, block["y"]+y    )
                    coeff_top  = self.coeff_buffer_getter("y", block["x"]+x+4  , block["y"]+y  -1)
                    nc = int((coeff_left + coeff_top + 1) // 2)
                    out_total_coeff = self.decode_residu_cavlc(block["x"]+x+4, block["y"]+y  , nc, "y")
                    logger.debug("out_total_coeff bit1: " + str(out_total_coeff))
                    self.coeff_buffer_setter("y", block["x"]+x+4, block["y"]+y  , out_total_coeff)
                else:
                    self.coeff_buffer_setter("y", block["x"]+x+4, block["y"]+y  , 0)

                if residu_mask & 4 != 0:
                    coeff_left = self.coeff_buffer_getter("y", block["x"]+x  -1, block["y"]+y+4  )
                    coeff_top  = self.coeff_buffer_getter("y", block["x"]+x    , block["y"]+y+4-1)
                    nc = int((coeff_left + coeff_top + 1) // 2)
                    out_total_coeff = self.decode_residu_cavlc(block["x"]+x  , block["y"]+y+4, nc, "y")
                    logger.debug("out_total_coeff bit2: " + str(out_total_coeff))
                    self.coeff_buffer_setter("y", block["x"]+x  , block["y"]+y+4, out_total_coeff)
                else:
                    self.coeff_buffer_setter("y", block["x"]+x  , block["y"]+y+4, 0)

                if residu_mask & 8 != 0:
                    coeff_left = self.coeff_buffer_getter("y", block["x"]+x+4-1, block["y"]+y+4  )
                    coeff_top  = self.coeff_buffer_getter("y", block["x"]+x+4  , block["y"]+y+4-1)
                    nc = int((coeff_left + coeff_top + 1) // 2)
                    out_total_coeff = self.decode_residu_cavlc(block["x"]+x+4, block["y"]+y+4, nc, "y")
                    logger.debug("out_total_coeff bit3: " + str(out_total_coeff))
                    self.coeff_buffer_setter("y", block["x"]+x+4, block["y"]+y+4, out_total_coeff)
                else:
                    self.coeff_buffer_setter("y", block["x"]+x+4, block["y"]+y+4, 0)

                if residu_mask & 16 != 0:
                    coeff_left = self.coeff_buffer_getter("uv", block["x"]+x-1, block["y"]+y  )
                    coeff_top  = self.coeff_buffer_getter("uv", block["x"]+x  , block["y"]+y-1)
                    nc = int((coeff_left + coeff_top + 1) // 2)
                    logger.debug("nc: " + str(nc))
                    out_total_coeff_u = self.decode_residu_cavlc(block["x"]+x, block["y"]+y, nc, "u")
                    out_total_coeff_v = self.decode_residu_cavlc(block["x"]+x, block["y"]+y, nc, "v")
                    out_total_coeff = int((out_total_coeff_u + out_total_coeff_v + 1) // 2)
                    logger.debug("out_total_coeff bit4: " + str(out_total_coeff))
                    self.coeff_buffer_setter("uv", block["x"]+x, block["y"]+y, out_total_coeff)
                else:
                    self.coeff_buffer_setter("uv", block["x"]+x, block["y"]+y, 0)


    def decode_residu_cavlc(self, x, y, nc, plane):
        coeff_token = self.reader.vlc2(vlc.coeff_token_vlc[ff_h264_cavlc_coeff_token_table_index[nc]])
        logger.debug("coeff_token: " + str(coeff_token))
        if coeff_token == -1:
            raise RuntimeError("invalid vlc")

        trailing_ones = coeff_token & 3
        total_coeff   = coeff_token >> 2
        out_total_coeff = total_coeff
        if total_coeff == 0:
            return out_total_coeff

        level = []
        if total_coeff == 16:
            zeros_left = 0
        else:
            zeros_left = self.reader.vlc2(vlc.total_zeros_vlc[total_coeff])
            logger.debug("zeros_left: " + str(zeros_left))
            for i in range(16 - (total_coeff + zeros_left)):
                level.insert(0, 0)

        suffix_length = 0
        while True:
            if trailing_ones > 0:
                trailing_ones -= 1
                level.insert(0, [1, -1][self.reader.bit()])
            else:
                level_prefix = 0
                while self.reader.bit() == 0:
                    level_prefix += 1

                if level_prefix == 15:
                    level_suffix = self.reader.int_from_bits(11)
                else:
                    level_suffix = self.reader.int_from_bits(suffix_length)

                level_code = (level_prefix << suffix_length) + level_suffix + 1

                suffix_length += 1 if level_code > ff_h264_cavlc_suffix_limit[suffix_length + 1] else 0

                if self.reader.bit() == 1:
                    level_code = -level_code
                level.insert(0, level_code)

            total_coeff -= 1
            if total_coeff == 0:
                break

            if zeros_left == 0:
                continue

            if zeros_left < 7:
                run_before = self.reader.vlc2(vlc.run_vlc[zeros_left])
            else:
                run_before = self.reader.vlc2(vlc.run7_vlc)

            zeros_left -= run_before
            for i in range(run_before):
                level.insert(0, 0)

        for i in range(zeros_left):
            level.insert(0, 0)

        logger.debug(level)

        self.decode_dct(x, y, plane, level)
        return out_total_coeff


    def decode_dct(self, x, y, plane, level):
        dct = [None] * len(zigzag_scan)

        # dezigzag
        for i, z in enumerate(zigzag_scan):
            dct[z] = level[i]

        # dequantize
        for i in range(16):
            dct[i] *= self.vframe.qtab[(i & 1) + ((i >> 2) & 1)]

        # h264_idct_add
        step = get_step(plane)

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


    def clear_total_coeff(self, block):
        for y in range(0, block["h"], 8):
            for x in range(0, block["w"], 8):
                self.coeff_buffer_setter("y", block["x"]+x  , block["y"]+y  , 0)
                self.coeff_buffer_setter("y", block["x"]+x  , block["y"]+y+4, 0)
                self.coeff_buffer_setter("y", block["x"]+x+4, block["y"]+y  , 0)
                self.coeff_buffer_setter("y", block["x"]+x+4, block["y"]+y+4, 0)
                self.coeff_buffer_setter("uv", block["x"]+x, block["y"]+y, 0)


    def decode_mb(self, block, pred_vec):
        logger.debug(block)
        mode = self.reader.unsigned_expgolomb()
        logger.debug(mode)
        if mode == 0: # v-split, no residu
            if block["w"] == 2:
                raise RuntimeError("cannot v-split block further")
            self.decode_mb(block_half_left(block), pred_vec)
            self.decode_mb(block_half_right(block), pred_vec)
            if block["w"] == 8 and block["h"] >= 8:
                self.clear_total_coeff(block)
        elif mode == 1: # no delta, no residu, ref 0
            self.predict_inter(block, pred_vec, False, self.vframe.ref_vframes[0])
            if block["w"] >= 8 and block["h"] >= 8:
                self.clear_total_coeff(block)
        elif mode == 2: # h-split, no residu
            if block["h"] == 2:
                raise RuntimeError("cannot h-split block further")
            self.decode_mb(block_half_up(block), pred_vec)
            self.decode_mb(block_half_down(block), pred_vec)
            if block["w"] >= 8 and block["h"] == 8:
                self.clear_total_coeff(block)
        elif mode == 3: # unpredicted delta ref0 + dc offset, no residu
            self.predict_inter_dc(block)
            if block["w"] >= 8 and block["h"] >= 8:
                self.clear_total_coeff(block)
        elif mode == 4: # delta, no residu, ref 0
            self.predict_inter(block, pred_vec, True, self.vframe.ref_vframes[0])
            if block["w"] >= 8 and block["h"] >= 8:
                self.clear_total_coeff(block)
        elif mode == 5: # delta, no residu, ref 1
            self.predict_inter(block, pred_vec, True, self.vframe.ref_vframes[1])
            if block["w"] >= 8 and block["h"] >= 8:
                self.clear_total_coeff(block)
        elif mode == 6: # delta, no residu, ref 2
            self.predict_inter(block, pred_vec, True, self.vframe.ref_vframes[2])
            if block["w"] >= 8 and block["h"] >= 8:
                self.clear_total_coeff(block)
        elif mode == 7: # plane, no residu
            self.predict_mb_plane(block)
            if block["w"] >= 8 and block["h"] >= 8:
                self.clear_total_coeff(block)
        elif mode == 8: # v-split, residu
            if block["w"] == 2:
                raise RuntimeError("cannot v-split block further")
            self.decode_mb(block_half_left(block), pred_vec)
            self.decode_mb(block_half_right(block), pred_vec)
            self.decode_residu_blocks(block)
        elif mode == 9: # no delta, no residu, ref 1
            self.predict_inter(block, pred_vec, False, self.vframe.ref_vframes[1])
            if block["w"] >= 8 and block["h"] >= 8:
                self.clear_total_coeff(block)
        elif mode == 10: # unpredicted delta ref0 + dc offset, no residu
            self.predict_inter_dc(block)
            self.decode_residu_blocks(block)
        elif mode == 11: # predict notile, no residu
            self.predict_notile(block)
            if block["w"] >= 8 and block["h"] >= 8:
                self.clear_total_coeff(block)
        elif mode == 12: # no delta, residu, ref 0
            self.predict_inter(block, pred_vec, False, self.vframe.ref_vframes[0])
            self.decode_residu_blocks(block)
        elif mode == 13: # h-split, residu
            if block["h"] == 2:
                raise RuntimeError("cannot h-split block further")
            self.decode_mb(block_half_up(block), pred_vec)
            self.decode_mb(block_half_down(block), pred_vec)
            self.decode_residu_blocks(block)
        elif mode == 14: # no delta, no residu, ref 2
            self.predict_inter(block, pred_vec, False, self.vframe.ref_vframes[2])
            if block["w"] >= 8 and block["h"] >= 8:
                self.clear_total_coeff(block)
        elif mode == 15: # predict4, no residu
            self.predict4(block)
            if block["w"] >= 8 and block["h"] >= 8:
                self.clear_total_coeff(block)
        elif mode == 16: # delta, residu, ref 0
            self.predict_inter(block, pred_vec, True, self.vframe.ref_vframes[0])
            self.decode_residu_blocks(block)
        elif mode == 17: # delta, residu, ref 1
            self.predict_inter(block, pred_vec, True, self.vframe.ref_vframes[1])
            self.decode_residu_blocks(block)
        elif mode == 18: # delta, residu, ref 2
            self.predict_inter(block, pred_vec, True, self.vframe.ref_vframes[2])
            self.decode_residu_blocks(block)
        elif mode == 19: # predict4, residu
            self.predict4(block)
            self.decode_residu_blocks(block)
        elif mode == 20: # no delta, residu, ref 1
            self.predict_inter(block, pred_vec, False, self.vframe.ref_vframes[1])
            self.decode_residu_blocks(block)
        elif mode == 21: # no delta, residu, ref 2
            self.predict_inter(block, pred_vec, False, self.vframe.ref_vframes[2])
            self.decode_residu_blocks(block)
        elif mode == 22: # predict notile, residu
            self.predict_notile(block)
            self.decode_residu_blocks(block)
        elif mode == 23: # plane, residu
            self.predict_mb_plane(block)
            self.decode_residu_blocks(block)
        else:
            raise RuntimeError("frame block mode " + str(mode) + " is greater than 23")


    def decode(self):
        self.coeff_buffers = {
            "y": np.zeros((self.vframe.height // 4 + 1, self.vframe.width // 4 + 1), dtype=np.uint16),
            "uv": np.zeros((self.vframe.height // 8 + 1, self.vframe.width // 8 + 1), dtype=np.uint16)
        }

        self.vectors = []
        for y in range((self.vframe.height // 16) + 1):
            self.vectors.append([])
            for x in range((self.vframe.width // 16) + 2):
                self.vectors[y].append({"x": 0, "y": 0})

        for y in range(0, self.vframe.height, 16):
            for x in range(0, self.vframe.width, 16):
                block = {
                    "x": x,
                    "y": y,
                    "w": 16,
                    "h": 16
                }

                pred_vec = {
                    "x": mid_pred(
                        self.vectors[(block["y"] // 16) + 1][(block["x"] // 16) + 0]["x"],
                        self.vectors[(block["y"] // 16) + 0][(block["x"] // 16) + 1]["x"],
                        self.vectors[(block["y"] // 16) + 0][(block["x"] // 16) + 2]["x"]
                    ),
                    "y": mid_pred(
                        self.vectors[(block["y"] // 16) + 1][(block["x"] // 16) + 0]["y"],
                        self.vectors[(block["y"] // 16) + 0][(block["x"] // 16) + 1]["y"],
                        self.vectors[(block["y"] // 16) + 0][(block["x"] // 16) + 2]["y"]
                    ),
                }
                logger.debug(block)
                self.decode_mb(block, pred_vec)

        # align with word
        while self.reader.offset % 2 != 0:
            self.reader.bit()

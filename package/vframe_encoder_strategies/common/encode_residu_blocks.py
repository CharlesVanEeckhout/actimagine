import logging

from ... import vlc
from ...frame_includes import *
from ...vframe_decoder import VFrameDecoder

logger = logging.getLogger(__name__)
logger.propagate = True # enable/disable


def encode_residu_blocks_check(self, block):
    check_result = {
        "check_results": [],
        "is_worth_encoding": False
    }
    for y in range(0, block["h"], 8):
        for x in range(0, block["w"], 8):
            cr = encode_residu_block_check(self, block["x"]+x, block["y"]+y)
            check_result["check_results"].append(cr)
            check_result["is_worth_encoding"] = (check_result["is_worth_encoding"] or cr["is_worth_encoding"])

    return check_result

def encode_residu_blocks_write(self, check_result):
    for cr in check_result["check_results"]:
        encode_residu_block_write(self, cr)


def encode_residu_block_check(self, x, y):
    check_result = {
        "x": x,
        "y": y
    }

    # calculate the levels
    check_result["level_y00"] = encode_dct(self, x  , y  , "y")
    check_result["level_y01"] = encode_dct(self, x+4, y  , "y")
    check_result["level_y10"] = encode_dct(self, x  , y+4, "y")
    check_result["level_y11"] = encode_dct(self, x+4, y+4, "y")
    check_result["level_u"] = encode_dct(self, x, y, "u")
    check_result["level_v"] = encode_dct(self, x, y, "v")

    check_result["residu_mask"] = \
        any(check_result["level_y00"]) * 1 + \
        any(check_result["level_y01"]) * 2 + \
        any(check_result["level_y10"]) * 4 + \
        any(check_result["level_y11"]) * 8 + \
        any(check_result["level_u"] + check_result["level_v"]) * 16

    check_result["is_worth_encoding"] = (check_result["residu_mask"] != 0)

    return check_result

def encode_residu_block_write(self, check_result):
    x = check_result["x"]
    y = check_result["y"]
    level_y00 = check_result["level_y00"]
    level_y01 = check_result["level_y01"]
    level_y10 = check_result["level_y10"]
    level_y11 = check_result["level_y11"]
    level_u = check_result["level_u"]
    level_v = check_result["level_v"]

    # apply levels to actual_plane_buffers
    VFrameDecoder.decode_dct(self, x  , y  , "y", level_y00)
    VFrameDecoder.decode_dct(self, x+4, y  , "y", level_y01)
    VFrameDecoder.decode_dct(self, x  , y+4, "y", level_y10)
    VFrameDecoder.decode_dct(self, x+4, y+4, "y", level_y11)
    VFrameDecoder.decode_dct(self, x, y, "u", level_u)
    VFrameDecoder.decode_dct(self, x, y, "v", level_v)

    # encode residu
    residu_mask = check_result["residu_mask"]
    residu_mask_tab_index = ff_actimagine_vx_residu_mask_new_tab.index(residu_mask)
    self.writer.unsigned_expgolomb(residu_mask_tab_index)

    if residu_mask & 1 != 0:
        coeff_left = self.coeff_buffer_getter("y", x  -1, y    )
        coeff_top  = self.coeff_buffer_getter("y", x    , y  -1)
        nc = int((coeff_left + coeff_top + 1) // 2)
        out_total_coeff = encode_residu_cavlc(self, x  , y  , level_y00, nc, "y")
        self.coeff_buffer_setter("y", x  , y  , out_total_coeff)
    else:
        self.coeff_buffer_setter("y", x  , y  , 0)

    if residu_mask & 2 != 0:
        coeff_left = self.coeff_buffer_getter("y", x+4-1, y    )
        coeff_top  = self.coeff_buffer_getter("y", x+4  , y  -1)
        nc = int((coeff_left + coeff_top + 1) // 2)
        out_total_coeff = encode_residu_cavlc(self, x+4, y  , level_y01, nc, "y")
        self.coeff_buffer_setter("y", x+4, y  , out_total_coeff)
    else:
        self.coeff_buffer_setter("y", x+4, y  , 0)

    if residu_mask & 4 != 0:
        coeff_left = self.coeff_buffer_getter("y", x  -1, y+4  )
        coeff_top  = self.coeff_buffer_getter("y", x    , y+4-1)
        nc = int((coeff_left + coeff_top + 1) // 2)
        out_total_coeff = encode_residu_cavlc(self, x  , y+4, level_y10, nc, "y")
        self.coeff_buffer_setter("y", x  , y+4, out_total_coeff)
    else:
        self.coeff_buffer_setter("y", x  , y+4, 0)

    if residu_mask & 8 != 0:
        coeff_left = self.coeff_buffer_getter("y", x+4-1, y+4  )
        coeff_top  = self.coeff_buffer_getter("y", x+4  , y+4-1)
        nc = int((coeff_left + coeff_top + 1) // 2)
        out_total_coeff = encode_residu_cavlc(self, x+4, y+4, level_y11, nc, "y")
        self.coeff_buffer_setter("y", x+4, y+4, out_total_coeff)
    else:
        self.coeff_buffer_setter("y", x+4, y+4, 0)

    if residu_mask & 16 != 0:
        coeff_left = self.coeff_buffer_getter("uv", x-1, y  )
        coeff_top  = self.coeff_buffer_getter("uv", x  , y-1)
        nc = int((coeff_left + coeff_top + 1) // 2)
        out_total_coeff_u = encode_residu_cavlc(self, x, y, level_u, nc, "u")
        out_total_coeff_v = encode_residu_cavlc(self, x, y, level_v, nc, "v")
        out_total_coeff = int((out_total_coeff_u + out_total_coeff_v + 1) // 2)
        self.coeff_buffer_setter("uv", x, y, out_total_coeff)
    else:
        self.coeff_buffer_setter("uv", x, y, 0)


def encode_dct(self, x, y, plane):
    step = get_step(plane)
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


def encode_residu_cavlc(self, x, y, level, nc, plane):
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


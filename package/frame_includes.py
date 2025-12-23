
ff_actimagine_vx_residu_mask_new_tab = [
    0x00, 0x08, 0x04, 0x02, 0x01, 0x1F, 0x0F, 0x0A,
    0x05, 0x0C, 0x03, 0x10, 0x0E, 0x0D, 0x0B, 0x07,
    0x09, 0x06, 0x1E, 0x1B, 0x1A, 0x1D, 0x17, 0x15,
    0x18, 0x12, 0x11, 0x1C, 0x14, 0x13, 0x16, 0x19
]

ff_h264_cavlc_coeff_token_table_index = [
    0, 0, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3
]

ff_h264_cavlc_suffix_limit = [
    0, 3, 6, 12, 24, 48, 0x8000
]

# ff_zigzag_scan with swapped 2bit
zigzag_scan = [
    0*4+0, 1*4+0, 0*4+1, 0*4+2,
    1*4+1, 2*4+0, 3*4+0, 2*4+1,
    1*4+2, 0*4+3, 1*4+3, 2*4+2,
    3*4+1, 3*4+2, 2*4+3, 3*4+3,
]

# 4x4 filters to be multiplied by coefficients to form the residu
dct_gradient = [
    [ 1.0,  1.0,  1.0,  1.0], # cos(0)
    [ 1.0,  0.5, -0.5, -1.0], # cos(pi*x)
    [ 1.0, -1.0, -1.0,  1.0], # cos(2pi*x)
    [ 0.5, -1.0,  1.0, -0.5], # cos(3pi*x)
]

def get_dct_filters(qtab):
    dct_filters = []
    for i in range(16):
        yres = i % 4
        xres = i // 4
        dct_filters.append([])
        for y in range(4):
            dct_filters[i].append([])
            for x in range(4):
                filter_value = dct_gradient[yres][y] * dct_gradient[xres][x]
                filter_value *= (1 << 6) / qtab[(yres & 1) + (xres & 1)]
                dct_filters[i][y].append(filter_value)
    return dct_filters


def mid_pred(a, b, c):
    return sorted([a, b, c])[1]

def av_clip_pixel(x):
    return min(max(0, x), 255)

def block_half_left(block):
    return {
        "x": block["x"],
        "y": block["y"],
        "w": block["w"]//2,
        "h": block["h"]
    }

def block_half_right(block):
    return {
        "x": block["x"] + block["w"]//2,
        "y": block["y"],
        "w": block["w"]//2,
        "h": block["h"]
    }

def block_half_up(block):
    return {
        "x": block["x"],
        "y": block["y"],
        "w": block["w"],
        "h": block["h"]//2
    }

def block_half_down(block):
    return {
        "x": block["x"],
        "y": block["y"] + block["h"]//2,
        "w": block["w"],
        "h": block["h"]//2
    }


def get_step(plane):
    return 1 if plane == "y" else 2

def plane_buffer_iterator(block, planes, callback):
    for plane in planes:
        step = get_step(plane)
        for y in range(block["y"], block["y"] + block["h"], step):
            for x in range(block["x"], block["x"] + block["w"], step):
                callback(x, y, plane)

# lpc
pulse_values_len = [
    42, 40, 32, 24
]
pulse_data_len = [
    8, 5, 4, 3
]



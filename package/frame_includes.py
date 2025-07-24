
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
];


def mid_pred(a, b, c):
    return sorted([a, b, c])[1]

def av_clip_pixel(x):
    return mid_pred(0, x, 255)

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


def plane_buffer_getter(plane_buffers, plane, x, y):
    step = 1 if plane == "y" else 2
    return plane_buffers[plane][y // step][x // step]

def plane_buffer_setter(plane_buffers, plane, x, y, value):
    step = 1 if plane == "y" else 2
    plane_buffers[plane][y // step][x // step] = value 

def plane_buffer_iterator(block, planes, callback, **kwargs):
    for plane in planes:
        step = 1 if plane == "y" else 2
        for y in range(block["y"], block["y"] + block["h"], step):
            for x in range(block["x"], block["x"] + block["w"], step):
                callback(x, y, plane, **kwargs)

def coeff_buffer_getter(coeff_buffers, plane, x, y):
    step = 1 if plane == "y" else 2
    return plane_buffer_getter(coeff_buffers, plane, x // 4 + step, y // 4 + step)
    
def coeff_buffer_setter(coeff_buffers, plane, x, y, value):
    step = 1 if plane == "y" else 2
    plane_buffer_setter(coeff_buffers, plane, x // 4 + step, y // 4 + step, value)


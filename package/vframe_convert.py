
import numpy as np
from PIL import Image


def convert_rgb_to_yuv(rgb):
    r, g, b = rgb
    y = (2*r + 4*g + b) / 7
    u = (b - y) / 2 + 128
    v = (r - y) / 2 + 128
    return (y, u, v)


def convert_yuv_to_rgb(yuv):
    y, u, v = yuv
    u -= 128
    v -= 128
    r = y + 2*v
    g = y - u//2 - v
    b = y + 2*u

    return (r, g, b)
    #return yuv


# may be unused
def convert_yuv_to_smpte170m(yuv):
    y, u, v = yuv
    u -= 128
    v -= 128
    yy = y + ((u * -68682 + v * 11534 + (1 << 19)) >> 20)
    uu = 128 + ((u * 1222325 + v * -4928) >> 20)
    vv = 128 + ((u * 49073 + v * 1487615) >> 20)
    return (yy, uu, vv)


def convert_frame_to_image(frame):
    a = np.zeros((frame['y'].shape[0], frame['y'].shape[1], 3), dtype=np.uint8)
    y, u, v = frame['y'].astype(np.int16), frame['u'].astype(np.int16), frame['v'].astype(np.int16)
    u -= 128
    v -= 128
    # stretch to correct shape
    u = np.repeat(np.repeat(u,2, axis=0), 2, axis=1)
    v = np.repeat(np.repeat(v,2, axis=0), 2, axis=1)
    # Red
    a[:,:,0] += np.clip(y + 2*v, 0, 255).astype(np.uint8)
    # Green
    a[:,:,1] += np.clip(y - u//2 - v, 0, 255).astype(np.uint8)
    # Blue
    a[:,:,2] += np.clip(y+2*u, 0, 255).astype(np.uint8)
    return Image.fromarray(a)


def convert_image_to_frame(image):
    if image.mode not in ['RGB', 'RGBA']:
        raise RuntimeError('image mode is not RGB')

    frame_width, frame_height = image.size
    if frame_width % 2 != 0 or frame_height % 2 != 0:
        raise RuntimeError('image resolution is not a multiple of 2')

    frame = {
        "y": np.zeros((frame_height, frame_width), dtype=np.int16),
        "u": np.zeros((frame_height, frame_width), dtype=np.int16),
        "v": np.zeros((frame_height, frame_width), dtype=np.int16)
    }
    a = np.asarray(image, dtype=np.int16)
    r, g, b = [a[:, :, i] for i in range(3)]
    frame["y"] += (2*r + 4*g + b + 3) // 7
    frame["u"] += (b - frame["y"]) // 2 + 128
    frame["v"] += (r - frame["y"]) // 2 + 128

    frame["u"] = (frame["u"][0::2, 0::2] + frame["u"][0::2, 1::2] + frame["u"][1::2, 0::2] + frame["u"][1::2, 1::2] + 2) // 4
    frame["v"] = (frame["v"][0::2, 0::2] + frame["v"][0::2, 1::2] + frame["v"][1::2, 0::2] + frame["v"][1::2, 1::2] + 2) // 4

    frame["y"] = frame["y"].astype(np.uint8)
    frame["u"] = frame["u"].astype(np.uint8)
    frame["v"] = frame["v"].astype(np.uint8)

    return frame


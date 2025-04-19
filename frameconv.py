
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
    image = Image.new("RGB", (frame["y"].shape[1], frame["y"].shape[0]))
    
    for y in range(frame["y"].shape[0]):
        for x in range(frame["y"].shape[1]):
            image.putpixel((x, y), convert_yuv_to_rgb((
                int(frame["y"][y][x]),
                int(frame["u"][y//2][x//2]),
                int(frame["v"][y//2][x//2])
            )))
    
    return image

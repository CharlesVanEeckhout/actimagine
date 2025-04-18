
import numpy as np
from PIL import Image


def convert_rgb_to_yuv(rgb):
    r, g, b = rgb
    y = (4*g + b + 2*r) / 7
    u = (b - y) / 2 + 128
    v = (r - y) / 2 + 128
    return (y, u, v)

def convert_yuv_to_rgb(yuv):
    y, u, v = yuv
    u -= 128
    v -= 128
    r = y + 2*v
    g = y - int(0.5*u) - v
    b = y + 2*u
    return (r, g, b)
    #return yuv

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


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


def convert_image_to_frame(image):
    if image.mode not in ["RGB", "RGBA"]:
        raise Exception("image mode is not RGB")

    frame_width, frame_height = image.size
    if frame_width % 2 != 0 or frame_height % 2 != 0:
        raise Exception("image's resolution is not a multiple of 2")

    frame = {
        "y": np.zeros((frame_height, frame_width), dtype=np.uint16),
        "u": np.zeros((frame_height // 2, frame_width // 2), dtype=np.uint16),
        "v": np.zeros((frame_height // 2, frame_width // 2), dtype=np.uint16)
    }

    for y in range(0, frame["y"].shape[0], 2):
        for x in range(0, frame["y"].shape[1], 2):
            yuv00 = convert_rgb_to_yuv(image.getpixel((x  , y  ))[:3])
            yuv01 = convert_rgb_to_yuv(image.getpixel((x+1, y  ))[:3])
            yuv10 = convert_rgb_to_yuv(image.getpixel((x  , y+1))[:3])
            yuv11 = convert_rgb_to_yuv(image.getpixel((x+1, y+1))[:3])
            frame["y"][y  ][x  ] = yuv00[0]
            frame["y"][y  ][x+1] = yuv01[0]
            frame["y"][y+1][x  ] = yuv10[0]
            frame["y"][y+1][x+1] = yuv11[0]
            frame["u"][y//2][x//2] = round((yuv00[1] + yuv01[1] + yuv10[1] + yuv11[1]) / 4)
            frame["v"][y//2][x//2] = round((yuv00[2] + yuv01[2] + yuv10[2] + yuv11[2]) / 4)

    return frame


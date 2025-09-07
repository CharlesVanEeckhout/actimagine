import numpy as np

from . import vframe_convert
from .vframe_decoder import VFrameDecoder
from .vframe_encoder import VFrameEncoder


class VFrame:
    def __init__(self, width, height, ref_vframes, qtab):
        self.width = width
        self.height = height
        self.ref_vframes = ref_vframes
        self.qtab = qtab
        self.plane_buffers = None


    def decode(self, reader):
        self.plane_buffers = {
            "y": np.zeros((self.height, self.width), dtype=np.uint16),
            "u": np.zeros((self.height // 2, self.width // 2), dtype=np.uint16),
            "v": np.zeros((self.height // 2, self.width // 2), dtype=np.uint16)
        }
        vframe_decoder = VFrameDecoder(self, reader)
        vframe_decoder.decode()


    def encode(self, writer, goal_plane_buffers, strategy):
        self.plane_buffers = {
            "y": np.zeros((self.height, self.width), dtype=np.uint16),
            "u": np.zeros((self.height // 2, self.width // 2), dtype=np.uint16),
            "v": np.zeros((self.height // 2, self.width // 2), dtype=np.uint16)
        }
        vframe_encoder = VFrameEncoder(self, writer, goal_plane_buffers, strategy)
        vframe_encoder.encode()


    def plane_buffer_getter(self, plane, x, y):
        step = 1 if plane == "y" else 2
        return int(self.plane_buffers[plane][y // step][x // step])


    def plane_buffer_setter(self, plane, x, y, value):
        step = 1 if plane == "y" else 2
        self.plane_buffers[plane][y // step][x // step] = value


    def export_buffers(self, filename):
        for plane in ["y", "u", "v"]:
            with open(f"{filename}_{plane}.bin", "wb") as f:
                for row in self.plane_buffers[plane]:
                    for pixel in row:
                        f.write(pixel.astype(np.uint8))


    def export_image(self, filename):
        test_image = vframe_convert.convert_frame_to_image(self.plane_buffers)
        test_image.save(filename)

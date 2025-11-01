import numpy as np

from ..frame_includes import *
from .common import *


class VFrameEncoderStrategyAbstract:
    def __init__(self):
        if type(self) == VFrameEncoderStrategyAbstract:
            raise TypeError("cannot instantiate abstract class " + str(type(self)))
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


    def encode_mb(self, block):
        raise NotImplementedError()


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

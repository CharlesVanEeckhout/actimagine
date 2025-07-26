
import numpy as np

from . import io
from . import vlc
from .frame_includes import *





class AudioFrameDecoder:
    def __init__(self):
        self.audio_extradata = None
        self.prev_frame_offset = None
        self.scale_modifier_index = None
        self.pulse_start_position = None
        self.pulse_packing_mode = None
        self.lpc_codebook_indexes = [None, None, None]
        self.data = []
        self.pulse_values = []
        self.samples = None


    def decode(self):
        lpc_filter_difference = []
        for k in range(8):
            coeff_sum = 0
            for i in range(3):
                coeff_sum += self.audio_extradata["lpc_codebooks"][i][self.lpc_codebook_indexes[i]][k]
            lpc_filter_difference.append(coeff_sum)
        print(lpc_filter_difference)
        print(self.pulse_start_position)
        print(self.prev_frame_offset)
        
        scale = self.audio_extradata["scale_modifiers"][self.scale_modifier_index]
        distance = [3, 3, 4, 5][self.pulse_packing_mode]
        if self.pulse_packing_mode == 0:
            for i in range(len(self.data)):
                for j in range(16 - 3, -1, -3):
                    self.pulse_values.append((self.data[i] >> j) & 0x7)
            self.pulse_values.append(
                (self.data[0] & 1) * 4 +
                (self.data[1] & 1) * 2 +
                (self.data[2] & 1) * 1
            )
            self.pulse_values.append(
                (self.data[3] & 1) * 4 +
                (self.data[4] & 1) * 2 +
                (self.data[5] & 1) * 1
            )
            
            self.pulse_values = [(val * 2 - 7) * scale for val in self.pulse_values]
        else:
            for i in range(len(self.data)):
                for j in range(16 - 2, -1, -2):
                    self.pulse_values.append((self.data[i] >> j) & 0x3)
            
            self.pulse_values = [(val * 2 - 3) * scale for val in self.pulse_values]
        
        self.samples = []
        for i in range(128):
            index = (i - self.pulse_start_position) / distance
            if index < 0 or index >= len(self.pulse_values) or (index % 1) != 0:
                self.samples.append(0)
                continue
            self.samples.append(self.pulse_values[int(index)])






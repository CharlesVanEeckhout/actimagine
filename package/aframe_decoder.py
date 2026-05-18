import math
import logging

from . import frame_includes
from .aframe_data_handler import AFrameDataHandler

logger = logging.getLogger(__name__)
logger.propagate = True # enable/disable


class AFrameDecoder:
    def __init__(self, aframe, reader):
        self.aframe = aframe
        self.reader = reader
        self.data_handler = AFrameDataHandler()

        self.pulse_values = None

        self.lpc_filter_quarters = None


    def decode(self):
        self.data_handler = AFrameDataHandler()
        self.data_handler.unpack_from_reader(self.reader)

        self.aframe.scale = self.aframe.audio_extradata['scale_initial']
        if self.aframe.prev_aframe is not None:
            if self.aframe.prev_aframe.prev_aframe is not None:
                prev_samples = self.aframe.prev_aframe.prev_aframe.samples
            else:
                prev_samples = [0]*128
            prev_samples += self.aframe.prev_aframe.samples
            if self.data_handler.prev_frame_offset != 0x7F:
                self.aframe.scale = self.aframe.prev_aframe.scale
        else:
            prev_samples = [0]*128*2

        self.aframe.scale = (self.aframe.scale * self.aframe.audio_extradata['scale_modifiers'][self.data_handler.scale_modifier_index]) // 0x2000
        print(self.aframe.scale)

        def read_sample(i):
            assert i >= -len(prev_samples) and i < 128
            if i < 0:
                return prev_samples[len(prev_samples) + i]
            else:
                return self.samples[i]

        if self.aframe.scale > 0x0FFFFFFF: # debug failsafe to be removed
            self.aframe.scale //= 0x10


        distance = self.data_handler.get_pulse_distance()
        self.pulse_values = [val * self.aframe.scale for val in self.data_handler.pulse_values]

        self.aframe.pulses = []
        for i in range(128):
            index = (i - self.data_handler.pulse_start_position) / distance
            pulse = 0
            if index >= 0 and index < len(self.pulse_values) and (index % 1) == 0:
                pulse = self.pulse_values[int(index)]
            self.aframe.pulses.append(pulse)
        if self.data_handler.prev_frame_offset < 0x7E:
            for i in range(0x7E-self.data_handler.prev_frame_offset, 128):
                self.aframe.pulses[i-(0x7E-self.data_handler.prev_frame_offset)] += self.aframe.prev_aframe.pulses[i]


        if self.data_handler.prev_frame_offset == 0x7F:
            # intra frame
            self.aframe.lpc_filter = self.aframe.audio_extradata['lpc_base'].copy()
        else:
            # inter frame
            if self.aframe.prev_aframe is None:
                raise RuntimeError('inter aframe has no previous aframe')
            self.aframe.lpc_filter = self.aframe.prev_aframe.lpc_filter.copy()

        lpc_filter_difference = []
        for k in range(8):
            coeff_sum = 0
            for i in range(3):
                coeff_sum += self.aframe.audio_extradata['lpc_codebooks'][i][self.data_handler.lpc_codebook_indexes[i]][k]
            lpc_filter_difference.append(coeff_sum)
        logger.debug(lpc_filter_difference)
        logger.debug(self.data_handler.pulse_start_position)
        logger.debug(self.data_handler.prev_frame_offset)
        
        for i in range(len(self.aframe.lpc_filter)):
            self.aframe.lpc_filter[i] += lpc_filter_difference[i]
        
        self.aframe.prev_sample_influence = []
        for i in range(8):
            coeff = self.aframe.lpc_filter[i]
            self.aframe.prev_sample_influence = [
                self.aframe.prev_sample_influence[j] + ((self.aframe.prev_sample_influence[i-j-1] * coeff) // 0x8000)
                for j in range(i)
            ]
            self.aframe.prev_sample_influence.append(coeff)
        self.aframe.prev_sample_influence = [-(p // 2) for p in self.aframe.prev_sample_influence]

        self.prev_sample_influence_quarters = [[], [], [], []]
        if self.data_handler.prev_frame_offset != 0x7F:
            # inter frame
            for i in range(len(self.aframe.lpc_filter)):
                self.prev_sample_influence_quarters[3] = self.aframe.prev_sample_influence[:]
                self.prev_sample_influence_quarters[1] = [
                    (self.aframe.prev_aframe.prev_sample_influence[j] + self.prev_sample_influence_quarters[3][j]) // 2
                    for j in range(len(self.aframe.prev_sample_influence))
                ]
                self.prev_sample_influence_quarters[0] = [
                    (self.aframe.prev_aframe.prev_sample_influence[j] + self.prev_sample_influence_quarters[1][j]) // 2
                    for j in range(len(self.aframe.prev_sample_influence))
                ]
                self.prev_sample_influence_quarters[2] = [
                    (self.prev_sample_influence_quarters[1][j] + self.prev_sample_influence_quarters[3][j]) // 2
                    for j in range(len(self.aframe.prev_sample_influence))
                ]
        else:
            # intra frame
            for i in range(len(self.aframe.lpc_filter)):
                self.prev_sample_influence_quarters[0] = self.aframe.prev_sample_influence[:]
                self.prev_sample_influence_quarters[1] = self.prev_sample_influence_quarters[0]
                self.prev_sample_influence_quarters[2] = self.prev_sample_influence_quarters[0]
                self.prev_sample_influence_quarters[3] = self.prev_sample_influence_quarters[0]


        if self.data_handler.prev_frame_offset < 0x7E:
            self.samples = []
            for i in range(128):
                volume = min(8, i+1, 128-i)
                self.samples.append(read_sample(i - 128 - 1 - self.data_handler.prev_frame_offset) * volume // 16)
        else:
            self.samples = [0]*128

        for i in range(128):
            prev_sample_influence = self.prev_sample_influence_quarters[i * 4 // 128]
            sample = self.aframe.pulses[i] * 0x4000
            for j in range(len(prev_sample_influence)):
                prev_sample = read_sample(i - 1 - j)
                sample += prev_sample * prev_sample_influence[j]
            sample //= 0x4000
            self.samples[i] += sample
        #print([f"{s&0xffffffff:08x}" for s in self.samples])
        self.aframe.samples = self.samples


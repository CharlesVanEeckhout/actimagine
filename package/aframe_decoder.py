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

        self.aframe.scale = self.aframe.audio_extradata['scale_initial'] * 0x2000
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
        
        self.aframe.scale *= self.aframe.audio_extradata['scale_modifiers'][self.data_handler.scale_modifier_index] / 0x2000

        def read_sample(i):
            assert i >= -len(prev_samples) and i < 128
            if i < 0:
                return prev_samples[len(prev_samples) + i]
            else:
                return self.samples[i]

        if self.aframe.scale > 0x0FFFFFFF: # debug failsafe to be removed
            self.aframe.scale /= 0x10


        distance = self.data_handler.get_pulse_distance()
        self.pulse_values = [val * self.aframe.scale for val in self.data_handler.pulse_values]

        self.aframe.pulses = []
        for i in range(0, 128):
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

        self.lpc_filter_quarters = [[], [], [], []]
        if self.data_handler.prev_frame_offset != 0x7F:
            # inter frame
            for i in range(len(self.aframe.lpc_filter)):
                self.lpc_filter_quarters[0].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i] * 1 // 4)
                self.lpc_filter_quarters[1].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i] * 2 // 4)
                self.lpc_filter_quarters[2].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i] * 3 // 4)
                self.lpc_filter_quarters[3].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i] * 4 // 4)
                self.aframe.lpc_filter[i] += lpc_filter_difference[i]
        else:
            # intra frame
            for i in range(len(self.aframe.lpc_filter)):
                self.lpc_filter_quarters[0].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i])
                self.lpc_filter_quarters[1].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i])
                self.lpc_filter_quarters[2].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i])
                self.lpc_filter_quarters[3].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i])
                self.aframe.lpc_filter[i] += lpc_filter_difference[i]


        if self.data_handler.prev_frame_offset < 0x7E:
            self.samples = []
            for i in range(0, 128):
                volume = min(8, i+1, 128-i)
                self.samples.append(read_sample(i - 128 - 1 - self.data_handler.prev_frame_offset) * volume // 16)
        else:
            self.samples = [0]*128
        
        for i in range(0, 128):
            lpc_filter_quarter = self.lpc_filter_quarters[i * 4 // 128]
            index = (i - self.data_handler.pulse_start_position) / distance
            sample = self.aframe.pulses[i]
            prev_sample_influence = [1.0, 0.0]
            for j in range(len(lpc_filter_quarter)):
                coeff = lpc_filter_quarter[j] / 0x8000
                prev_sample_influence = [prev_sample_influence[k] + prev_sample_influence[len(prev_sample_influence)-1-k]*coeff for k in range(len(prev_sample_influence))] + [0]
            for j in range(len(lpc_filter_quarter)):
                prev_sample = read_sample(i - 1 - j)
                sample -= prev_sample * prev_sample_influence[j+1]
            self.samples[i] += math.floor(sample)
        self.aframe.samples = self.samples


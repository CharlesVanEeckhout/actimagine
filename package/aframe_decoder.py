import logging

logger = logging.getLogger(__name__)
logger.propagate = True # enable/disable


class AFrameDecoder:
    def __init__(self, aframe, reader):
        self.aframe = aframe
        self.reader = reader
        self.prev_frame_offset = None
        self.scale_modifier_index = None
        self.pulse_start_position = None
        self.pulse_packing_mode = None
        self.lpc_codebook_indexes = None
        self.pulse_data = None
        self.pulse_values = None
        self.lpc_filter_quarters = None


    def decode(self):
        aframe_header_word1 = self.reader.int_from_bits(16)
        aframe_header_word2 = self.reader.int_from_bits(16)
        self.prev_frame_offset = (aframe_header_word1 >> 9) & 0x7f
        self.scale_modifier_index = (aframe_header_word1 >> 6) & 0x7
        self.pulse_start_position = (aframe_header_word2 >> 14) & 0x3
        self.pulse_packing_mode = (aframe_header_word2 >> 12) & 0x3
        self.lpc_codebook_indexes = [
            (aframe_header_word1 >> 0) & 0x3f,
            (aframe_header_word2 >> 6) & 0x3f,
            (aframe_header_word2 >> 0) & 0x3f
        ]
        self.pulse_data = []
        for i in range([8, 5, 4, 3][self.pulse_packing_mode]):
            self.pulse_data.append(self.reader.int_from_bits(16))


        scale = self.aframe.audio_extradata["scale_modifiers"][self.scale_modifier_index]
        distance = [3, 3, 4, 5][self.pulse_packing_mode]
        self.pulse_values = []
        if self.pulse_packing_mode == 0:
            for i in range(len(self.pulse_data)):
                for j in range(16 - 3, -1, -3):
                    self.pulse_values.append((self.pulse_data[i] >> j) & 0x7)
            self.pulse_values.append(
                (self.pulse_data[0] & 1) * 4 +
                (self.pulse_data[1] & 1) * 2 +
                (self.pulse_data[2] & 1) * 1
            )
            self.pulse_values.append(
                (self.pulse_data[3] & 1) * 4 +
                (self.pulse_data[4] & 1) * 2 +
                (self.pulse_data[5] & 1) * 1
            )

            self.pulse_values = [(val * 2 - 7) * scale for val in self.pulse_values]
        else:
            for i in range(len(self.pulse_data)):
                for j in range(16 - 2, -1, -2):
                    self.pulse_values.append((self.pulse_data[i] >> j) & 0x3)

            self.pulse_values = [(val * 2 - 3) * scale for val in self.pulse_values]


        self.aframe.lpc_filter = self.aframe.audio_extradata["lpc_base"].copy()
        if self.prev_frame_offset != 0x7f:
            # inter frame
            if self.aframe.prev_aframe is None:
                raise RuntimeError("inter aframe has no previous aframe")
            self.aframe.lpc_filter = self.aframe.prev_aframe.lpc_filter.copy()
        
        lpc_filter_difference = []
        for k in range(8):
            coeff_sum = 0
            for i in range(3):
                coeff_sum += self.aframe.audio_extradata["lpc_codebooks"][i][self.lpc_codebook_indexes[i]][k]
            lpc_filter_difference.append(coeff_sum)
        logger.debug(lpc_filter_difference)
        logger.debug(self.pulse_start_position)
        logger.debug(self.prev_frame_offset)

        self.lpc_filter_quarters = [[], [], [], []]
        if self.prev_frame_offset != 0x7f:
            # inter frame
            for i in range(len(self.aframe.lpc_filter)):
                self.lpc_filter_quarters[0].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i] * 1 // 4)
                self.lpc_filter_quarters[1].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i] * 2 // 4)
                self.lpc_filter_quarters[2].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i] * 3 // 4)
                self.lpc_filter_quarters[3].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i])
                self.aframe.lpc_filter[i] += lpc_filter_difference[i]
        else:
            # intra frame
            for i in range(len(self.aframe.lpc_filter)):
                self.lpc_filter_quarters[0].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i])
                self.lpc_filter_quarters[1].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i])
                self.lpc_filter_quarters[2].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i])
                self.lpc_filter_quarters[3].append(self.aframe.lpc_filter[i] + lpc_filter_difference[i])
                self.aframe.lpc_filter[i] += lpc_filter_difference[i]

        prev_samples = [0, 0, 0, 0, 0, 0, 0, 0]
        self.samples = []
        if self.prev_frame_offset < 0x7E:
            for i in range(0x7E-self.prev_frame_offset, 128):
                self.samples.append(self.aframe.prev_aframe.samples[i])
            prev_samples = []
            for i in range(120, 128):
                prev_samples.append(self.aframe.prev_aframe.samples[i])
        for i in range(len(self.samples), 128):
            lpc_filter_quarter = self.lpc_filter_quarters[i * 4 // 128]
            index = (i - self.pulse_start_position) / distance
            pulse = 0
            if index >= 0 and index < len(self.pulse_values) and (index % 1) == 0:
                pulse = self.pulse_values[int(index)]
            sample = pulse
            for j in range(len(lpc_filter_quarter)):
                prev_sample_index = i - 1 - j
                if prev_sample_index < 0:
                    prev_sample = prev_samples[8 + prev_sample_index]
                else:
                    prev_sample = self.samples[prev_sample_index]
                sample += prev_sample * lpc_filter_quarter[j] // 65536 # maybe??
            self.samples.append(sample)
        self.aframe.samples = self.samples

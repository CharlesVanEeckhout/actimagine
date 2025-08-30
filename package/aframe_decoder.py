

class AFrameDecoder:
    def __init__(self, aframe, reader):
        self.aframe = aframe
        self.reader = reader
        self.prev_frame_offset = None
        self.scale_modifier_index = None
        self.pulse_start_position = None
        self.pulse_packing_mode = None
        self.lpc_codebook_indexes = None
        self.pulse_values = None
        self.data = None


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
        self.data = []
        for i in range([8, 5, 4, 3][self.pulse_packing_mode]):
            self.data.append(self.reader.int_from_bits(16))

        lpc_filter_difference = []
        for k in range(8):
            coeff_sum = 0
            for i in range(3):
                coeff_sum += self.aframe.audio_extradata["lpc_codebooks"][i][self.lpc_codebook_indexes[i]][k]
            lpc_filter_difference.append(coeff_sum)
        print(lpc_filter_difference)
        print(self.pulse_start_position)
        print(self.prev_frame_offset)

        scale = self.aframe.audio_extradata["scale_modifiers"][self.scale_modifier_index]
        distance = [3, 3, 4, 5][self.pulse_packing_mode]
        self.pulse_values = []
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
        self.aframe.samples = self.samples

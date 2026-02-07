
from package import io


pulse_values_len = [
    42, 40, 32, 24
]
pulse_data_len = [
    8, 5, 4, 3
]


class AFrameDataHandler:
    def __init__(self):
        self.data = None

        self.prev_frame_offset = None
        self.scale_modifier_index = None
        self.pulse_start_position = None
        self.lpc_codebook_indexes = None
        self.pulse_values = None
    
    
    def unpack_pulse_values(self, pulse_packing_mode, pulse_data):
        self.pulse_values = []
        if pulse_packing_mode == 0:
            for i in range(len(pulse_data)):
                for j in range(16 - 3, -1, -3):
                    self.pulse_values.append((pulse_data[i] >> j) & 0x7)
            self.pulse_values.append(
                (pulse_data[0] & 1) * 4 +
                (pulse_data[1] & 1) * 2 +
                (pulse_data[2] & 1) * 1
            )
            self.pulse_values.append(
                (pulse_data[3] & 1) * 4 +
                (pulse_data[4] & 1) * 2 +
                (pulse_data[5] & 1) * 1
            )

            self.pulse_values = [(val * 2 - 7) for val in self.pulse_values]
        else:
            for i in range(len(pulse_data)):
                for j in range(16 - 2, -1, -2):
                    self.pulse_values.append((pulse_data[i] >> j) & 0x3)

            self.pulse_values = [(val * 2 - 3) for val in self.pulse_values]


    def pack_pulse_values(self, pulse_packing_mode):
        pulse_data = [0] * pulse_data_len[pulse_packing_mode]
        if pulse_packing_mode == 0:
            self.pulse_values = [(val + 7) // 2 for val in self.pulse_values]
            
            for i in range(len(pulse_data)):
                for j in range(5):
                    shift = 16 - 3 - 3 * j
                    pulse_data[i] += self.pulse_values[5*i + j] << shift
            pulse_data[0] += (self.pulse_values[40] >> 2) & 1
            pulse_data[1] += (self.pulse_values[40] >> 1) & 1
            pulse_data[2] += (self.pulse_values[40] >> 0) & 1
            pulse_data[3] += (self.pulse_values[41] >> 2) & 1
            pulse_data[4] += (self.pulse_values[41] >> 1) & 1
            pulse_data[5] += (self.pulse_values[41] >> 0) & 1
        else:
            self.pulse_values = [(val + 3) // 2 for val in self.pulse_values]
            
            for i in range(len(pulse_data)):
                for j in range(8):
                    shift = 16 - 2 - 2 * j
                    pulse_data[i] += self.pulse_values[8*i + j] << shift
        return pulse_data
    
    
    def unpack_header(self, aframe_header_word1, aframe_header_word2):
        self.prev_frame_offset = (aframe_header_word1 >> 9) & 0x7f
        self.scale_modifier_index = (aframe_header_word1 >> 6) & 0x7
        self.pulse_start_position = (aframe_header_word2 >> 14) & 0x3
        pulse_packing_mode = (aframe_header_word2 >> 12) & 0x3
        self.lpc_codebook_indexes = [
            (aframe_header_word1 >> 0) & 0x3f,
            (aframe_header_word2 >> 6) & 0x3f,
            (aframe_header_word2 >> 0) & 0x3f
        ]
        return pulse_packing_mode
    
    
    def pack_header(self, writer, pulse_packing_mode):
        aframe_header_word1 = \
            (self.prev_frame_offset << 9) + \
            (self.scale_modifier_index << 6) + \
            self.lpc_codebook_indexes[0]
        aframe_header_word2 = \
            (self.pulse_start_position << 14) + \
            (pulse_packing_mode << 12) + \
            (self.lpc_codebook_indexes[1] << 6) + \
            self.lpc_codebook_indexes[2]
        writer.int_to_bits(aframe_header_word1, 16)
        writer.int_to_bits(aframe_header_word2, 16)
    
    
    def unpack_from_reader(self, reader):
        aframe_header_word1 = reader.int_from_bits(16)
        aframe_header_word2 = reader.int_from_bits(16)
        pulse_packing_mode = self.unpack_header(aframe_header_word1, aframe_header_word2)
        pulse_data = []
        for i in range(pulse_data_len[pulse_packing_mode]):
            pulse_data.append(reader.int_from_bits(16))
        self.unpack_pulse_values(pulse_packing_mode, pulse_data)
    
    
    def pack(self):
        pulse_packing_mode = pulse_values_len.index(len(self.pulse_values))
        
        writer = io.BitStreamWriter()
        
        self.pack_header(writer, pulse_packing_mode)
        
        pulse_data = self.pack_pulse_values(pulse_packing_mode)
        for word in pulse_data:
            writer.int_to_bits(word, 16)
        
        self.data = writer.get_data_bytes()
        return self.data
    
    
    def get_pulse_packing_mode(self):
        return pulse_values_len.index(len(self.pulse_values))
    
    
    def get_pulse_distance(self):
        return [3, 3, 4, 5][self.get_pulse_packing_mode()]
    


from .aframe_decoder import AFrameDecoder


class AFrame:
    def __init__(self, audio_extradata, prev_aframe):
        self.samples = None
        self.lpc_filter = None
        self.audio_extradata = audio_extradata
        self.prev_aframe = prev_aframe


    def decode(self, reader):
        self.samples = []
        aframe_decoder = AFrameDecoder(self, reader)
        aframe_decoder.decode()


    def encode(self, writer):
        raise NotImplementedError()
        """prev_frame_offset = 0x7f # 0x00 to 0x7f
        scale_modifier_index = 0 # 0 to 7
        pulse_start_position = 0 # 0 to 3
        pulse_packing_mode = 3 # 0 to 3
        lpc_codebook_indexes = [
            0x00, # 0x00 to 0x3f
            0x00, # 0x00 to 0x3f
            0x00  # 0x00 to 0x3f
        ]
        aframe_header_word1 = (prev_frame_offset << 9) + (scale_modifier_index << 6) + lpc_codebook_indexes[0]
        aframe_header_word2 = (pulse_start_position << 14) + (pulse_packing_mode << 12) + (lpc_codebook_indexes[1] << 6) + lpc_codebook_indexes[2]
        writer.int_to_bits(aframe_header_word1, 16)
        writer.int_to_bits(aframe_header_word2, 16)
        
        pulse_data = [int(x) for x in "111111121212121212121212"]
        if len(pulse_data) != 24:
            raise Exception("not 24 pulse")
        
        pulse_data = [pulse_data[i:i+8] for i in range(0, len(pulse_data), 8)]
        for i, word in enumerate(pulse_data):
            word = sum([(x << (14-j*2)) for j, x in enumerate(word)])
            writer.int_to_bits(word, 16)"""
        

import sys
sys.path.append('..')

from package import io
from package import aframe

def get_audio_extradata():
    audio_extradata = []

    audio_extradata["lpc_codebooks"] = []
    for i in range(3):
        audio_extradata["lpc_codebooks"].append([])
        for j in range(64):
            audio_extradata["lpc_codebooks"][i].append([0, 0, 0, 0, 0, 0, 0, 0])

    audio_extradata["scale_modifiers"] = [0, 0, 0, 0, 0, 0, 0, 0]

    audio_extradata["lpc_base"] = [0, 0, 0, 0, 0, 0, 0, 0]

    audio_extradata["scale_initial"] = 0x10000000

    return audio_extradata


def get_aframe_data():
    writer = io.BitStreamWriter()
    
    prev_frame_offset = 0x7f # 0x00 to 0x7f
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
        writer.int_to_bits(word, 16)
    
    return writer.get_data_bytes()


def lpc_test(expected_results, tested_lpc_coeff):
    audio_extradata = get_audio_extradata()
    aframe = AFrame(audio_extradata, None)
    reader = 


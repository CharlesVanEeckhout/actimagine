import sys
import numpy as np
sys.path.append('..')

from package import io
from package.aframe import AFrame
from package.frame_includes import *
from package.aframe_decoder import AFrameDecoder


def get_default_audio_extradata():
    audio_extradata = {}

    audio_extradata["lpc_codebooks"] = []
    for i in range(3):
        audio_extradata["lpc_codebooks"].append([])
        for j in range(64):
            audio_extradata["lpc_codebooks"][i].append([0, 0, 0, 0, 0, 0, 0, 0])

    audio_extradata["scale_modifiers"] = [1, 0, 0, 0, 0, 0, 0, 0]

    audio_extradata["lpc_base"] = [0, 0, 0, 0, 0, 0, 0, 0]

    audio_extradata["scale_initial"] = 0x08000000 # 0x10000000 is max

    return audio_extradata


def get_default_aframe_data_object():
    aframe_data_object = {}
    
    aframe_data_object["prev_frame_offset"] = 0x7f # 0x00 to 0x7f
    aframe_data_object["scale_modifier_index"] = 0 # 0 to 7
    aframe_data_object["pulse_start_position"] = 0 # 0 to 3
    aframe_data_object["lpc_codebook_indexes"] = [
        0x00, # 0x00 to 0x3f
        0x00, # 0x00 to 0x3f
        0x00  # 0x00 to 0x3f
    ]
    
    aframe_data_object["pulse_values"] = [2 * int(x) - 3 for x in "111111121212121212121212"]
    
    return aframe_data_object


def get_aframe_data(aframe_data_object):
    pulse_packing_mode = pulse_values_len.index(len(aframe_data_object["pulse_values"]))
    
    writer = io.BitStreamWriter()
    
    aframe_header_word1 = \
        (aframe_data_object["prev_frame_offset"] << 9) + \
        (aframe_data_object["scale_modifier_index"] << 6) + \
        aframe_data_object["lpc_codebook_indexes"][0]
    aframe_header_word2 = \
        (aframe_data_object["pulse_start_position"] << 14) + \
        (pulse_packing_mode << 12) + \
        (aframe_data_object["lpc_codebook_indexes"][1] << 6) + \
        aframe_data_object["lpc_codebook_indexes"][2]
    writer.int_to_bits(aframe_header_word1, 16)
    writer.int_to_bits(aframe_header_word2, 16)
    
    pulse_data = AFrameDecoder.pack_pulse_values(aframe_data_object["pulse_values"])
    for word in pulse_data:
        writer.int_to_bits(word, 16)
    
    return writer.get_data_bytes()


def lpc_test(expected_samples, callback_context_tweaker):
    audio_extradata = get_default_audio_extradata()
    aframe_data_object = get_default_aframe_data_object()
    callback_context_tweaker(aframe_data_object, audio_extradata)
    aframe_data = get_aframe_data(aframe_data_object)
    print(list(aframe_data))
    
    aframe = AFrame(audio_extradata, None)
    reader = io.DataReader()
    # aframe decode expects the word to be inverted
    reader.set_data_bytes([byte for i in range(0, len(aframe_data)-1, 2) for byte in reversed(aframe_data[i:i+2])], bitorder="big")
    aframe.decode(reader)
    samples = np.array(aframe.samples) / 0x2000
    samples = list(np.clip(np.fix(samples), -0x8000, 0x7fff))
    
    if samples != expected_samples:
        raise Exception("samples " + str(aframe.samples) + " is different from expected samples " + str(expected_samples))


import sys
import numpy as np
sys.path.append('..')

from package import io
from package.aframe import AFrame
from package.frame_includes import *
from package.aframe_decoder import AFrameDecoder
from package.aframe_data_handler import AFrameDataHandler


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


def get_default_aframe_data_handler():
    aframe_data_handler = AFrameDataHandler()
    
    aframe_data_handler.prev_frame_offset = 0x7f # 0x00 to 0x7f
    aframe_data_handler.scale_modifier_index = 0 # 0 to 7
    aframe_data_handler.pulse_start_position = 0 # 0 to 3
    aframe_data_handler.lpc_codebook_indexes = [
        0x00, # 0x00 to 0x3f
        0x00, # 0x00 to 0x3f
        0x00  # 0x00 to 0x3f
    ]
    aframe_data_handler.pulse_values = [int(x) * 2 - 3 for x in "111111121212121212121212"]
    
    return aframe_data_handler


def lpc_test(expected_samples, callback_context_tweaker):
    audio_extradata = get_default_audio_extradata()
    aframe_data_handlers = callback_context_tweaker(get_default_aframe_data_handler, audio_extradata)
    aframe_data_list = [aframe_data_handler.pack() for aframe_data_handler in aframe_data_handlers]
    
    samples = []
    prev_aframe = None
    for aframe_data in aframe_data_list:
        aframe = AFrame(audio_extradata, prev_aframe)
        reader = io.DataReader()
        # aframe decode expects the word to be inverted
        reader.set_data_bytes([byte for i in range(0, len(aframe_data)-1, 2) for byte in reversed(aframe_data[i:i+2])], bitorder="big")
        aframe.decode(reader)
        s = np.array(aframe.samples) / 0x2000
        s = list(np.clip(np.fix(s), -0x8000, 0x7fff))
        samples += s
        prev_aframe = aframe
    
    if samples != expected_samples:
        raise Exception("samples " + str(aframe.samples) + " is different from expected samples " + str(expected_samples))


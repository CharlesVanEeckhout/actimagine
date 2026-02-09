
from ..aframe import AFrame
from ..aframe_data_handler import AFrameDataHandler


class SimplePulseExtend:
    def __init__(self):
        pass


    def init_audio_extradata(self, audio_extradata):
        audio_extradata["lpc_codebooks"] = []
        for i in range(3):
            audio_extradata["lpc_codebooks"].append([])
            for j in range(64):
                audio_extradata["lpc_codebooks"][i].append([0, 0, 0, 0, 0, 0, 0, 0])

        audio_extradata["scale_modifiers"] = [int(0x2000*(2**(-i))) for i in range(8)]
        print(audio_extradata["scale_modifiers"])

        audio_extradata["lpc_base"] = [-22420, 12486, 4995, -10789, 10079, -2117, -3497, 1811]

        audio_extradata["scale_initial"] = 0x10000000//0x2000//3 # 0x10000000 is max


    def encode(self, aframe_encoder):
        aframe = aframe_encoder.aframe
        audio_extradata = aframe.audio_extradata
        aframe_data_handler = AFrameDataHandler()

        aframe_data_handler.prev_frame_offset = 0x7f # 0x00 to 0x7f
        aframe_data_handler.pulse_start_position = 0 # 0 to 3
        aframe_data_handler.lpc_codebook_indexes = [
            0x00, # 0x00 to 0x3f
            0x00, # 0x00 to 0x3f
            0x00  # 0x00 to 0x3f
        ]

        pulses = [int(aframe_encoder.goal_samples[3*i]) for i in range(40)]
        max_amplitude = 0
        for p in pulses:
            max_amplitude = max(max_amplitude, abs(p))
        for i in range(len(pulses)):
            pulses[i] = min(max(((pulses[i] * 2) // max_amplitude) * 2 + 1, -3), 3)
        aframe_data_handler.pulse_values = pulses

        for i, threshold in enumerate([int(0x5000*(2**(-i))) for i in range(8)]):
            if max_amplitude >= threshold:
                aframe_data_handler.scale_modifier_index = i
                break
        if aframe_data_handler.scale_modifier_index is None:
            aframe_data_handler.prev_frame_offset = 0x7e # zeroes
            aframe_data_handler.scale_modifier_index = 7
        print(audio_extradata["scale_modifiers"][aframe_data_handler.scale_modifier_index])

        aframe_data_handler.pack_to_writer(aframe_encoder.writer)


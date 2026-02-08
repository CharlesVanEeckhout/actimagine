
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

        audio_extradata["scale_modifiers"] = [0x7fff, 0x4000, 0x2000, 0x1000, 0x0800, 0, 0, 0]

        audio_extradata["lpc_base"] = [-22420, 12486, 4995, -10789, 10079, -2117, -3497, 1811]

        audio_extradata["scale_initial"] = 0x10000000//0x2000//7 # 0x10000000 is max


    def encode(self, aframe_encoder):
        aframe = aframe_encoder.aframe
        audio_extradata = aframe.audio_extradata
        aframe_data_handler = AFrameDataHandler()
        
        aframe_data_handler.prev_frame_offset = 0x7f # 0x00 to 0x7f
        aframe_data_handler.scale_modifier_index = 0 # 0 to 7
        aframe_data_handler.pulse_start_position = 0 # 0 to 3
        aframe_data_handler.lpc_codebook_indexes = [
            0x00, # 0x00 to 0x3f
            0x00, # 0x00 to 0x3f
            0x00  # 0x00 to 0x3f
        ]

        if aframe.prev_aframe is not None:
            prev_scale = aframe.prev_aframe.scale
        else:
            prev_scale = aframe.audio_extradata["scale_initial"] * 0x2000
        prev_scale /= 0x2000

        pulses = [int(aframe_encoder.goal_samples[3*i]) for i in range(42)]
        max_amplitude = 0
        for p in pulses:
            max_amplitude = max(max_amplitude, abs(p))
        for i in range(len(pulses)):
            pulses[i] = min(max(((pulses[i] * 4) // max_amplitude) * 2 + 1, -7), 7)
        aframe_data_handler.pulse_values = pulses

        scale_modifier_value = 0x2000 * max_amplitude / prev_scale
        for i, threshold in enumerate([0x5000, 0x2800, 0x1400, 0x0A00, -1]):
            if scale_modifier_value >= threshold:
                aframe_data_handler.scale_modifier_index = i
                break
        aframe.scale = prev_scale * audio_extradata["scale_modifiers"][aframe_data_handler.scale_modifier_index]

        aframe_data = aframe_data_handler.pack()
        aframe_encoder.writer.bytes(aframe_data)
            
            
            

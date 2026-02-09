def callback_base(get_default_aframe_data_handler, audio_extradata):
    aframe_data_handler = get_default_aframe_data_handler()
    return [aframe_data_handler]


def callback_scale_and_rounding(get_default_aframe_data_handler, audio_extradata, scale_initial, scale_modifier):
    aframe_data_handler = get_default_aframe_data_handler()
    audio_extradata["scale_initial"] = scale_initial # 0x10000000 is max
    audio_extradata["scale_modifiers"][0] = scale_modifier
    return [aframe_data_handler]


def callback_multiframe(get_default_aframe_data_handler, audio_extradata, frame_qty):
    aframe_data_handler = get_default_aframe_data_handler()
    aframe_data_handler.pulse_values = [int(x) * 2 - 3 for x in "1212121212121212121212121212121212121212"]
    aframe_data_handler.scale_modifier_index = 3
    audio_extradata["scale_initial"] = 0x10000000//0x2000//7
    audio_extradata["scale_modifiers"] = [0x8000, 0x4000, 0x2000, 0x1000, 0x0800, 0, 0, 0]
    return [aframe_data_handler]*frame_qty


def callback_simple_pulseextend_strat(get_default_aframe_data_handler, audio_extradata):
    aframe_data_handler = get_default_aframe_data_handler()
    aframe_data_handler.pulse_values = [int(x) * 2 - 7 for x in "343434340123456734343434343434343434343434"]
    #audio_extradata["lpc_base"] = [-22420, 12486, 4995, -10789, 10079, -2117, -3497, 1811]
    aframe_data_handler.scale_modifier_index = 2
    audio_extradata["scale_initial"] = 0x10000000//0x2000//7
    audio_extradata["scale_modifiers"] = [0x8000, 0x4000, 0x2000, 0x1000, 0x0800, 0, 0, 0]
    return [aframe_data_handler]*2


lpc_test_context = {
    "base": [
        lambda afr, aex: callback_base(afr, aex),
    ],
    "scale_and_rounding": [
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x07ffffff, 1),
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x08000001, 1),
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x08001000, 1),
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x08002000, 1),
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x08000000//0x2000, 0x2000),
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x08000000//0x8000, 0x8000),
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x08000000//0x8000, 0xffff),
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x10000000//0x2000//7, 0x2000),
    ],
    "multiframe": [
        lambda afr, aex: callback_multiframe(afr, aex, 2),
        lambda afr, aex: callback_multiframe(afr, aex, 5),
    ],
    "simple_pulseextend_strat": [
        lambda afr, aex: callback_simple_pulseextend_strat(afr, aex),
    ],
}


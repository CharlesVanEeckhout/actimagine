def callback_base(get_default_aframe_data_handler, audio_extradata):
    aframe_data_handler = get_default_aframe_data_handler()
    return [aframe_data_handler]


def callback_scale_and_rounding(get_default_aframe_data_handler, audio_extradata, scale_initial):
    aframe_data_handler = get_default_aframe_data_handler()
    audio_extradata["scale_initial"] = scale_initial # 0x10000000 is max
    return [aframe_data_handler]


def callback_simple_pulseextend_strat(get_default_aframe_data_handler, audio_extradata):
    aframe_data_handler = get_default_aframe_data_handler()
    aframe_data_handler.pulse_values = [int(x) * 2 - 7 for x in "343434343434343434343434343434343434343434"]
    audio_extradata["lpc_base"] = [-22420, 12486, 4995, -10789, 10079, -2117, -3497, 1811]
    return [aframe_data_handler]


lpc_test_context = {
    "base": [
        lambda afr, aex: callback_base(afr, aex),
    ],
    "scale_and_rounding": [
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x07ffffff),
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x08000001),
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x08001000),
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x08002000),
    ],
    "simple_pulseextend_strat": [
        lambda afr, aex: callback_simple_pulseextend_strat(afr, aex),
    ],
}


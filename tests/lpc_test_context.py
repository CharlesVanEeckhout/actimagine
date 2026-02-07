def callback_scale_and_rounding(aframe_data_object, audio_extradata, scale_initial):
    audio_extradata["scale_initial"] = scale_initial # 0x10000000 is max


def callback_simple_pulseextend_strat(aframe_data_object, audio_extradata):
    aframe_data_object["pulse_values"] = [int(x) * 2 - 7 for x in "343434343434343434343434343434343434343434"]
    #aframe_data_object["pulse_values"] = [2 * int(x) - 3 for x in "111111121212121212121212"]
    audio_extradata["lpc_base"] = [-22420, 12486, 4995, -10789, 10079, -2117, -3497, 1811]


lpc_test_context = {
    "base": [
        lambda afr, aex: None,
    ],
    "scale_and_rounding": [
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x07ffffff),
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x08000001),
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x08001000),
        lambda afr, aex: callback_scale_and_rounding(afr, aex, 0x08002000),
    ],
    "simple_pulseextend_strat": [
        lambda afr, aex: callback_simple_degree0_strat(afr, aex),
    ],
}


def callback_scale_and_rounding(aframe_data_object, audio_extradata, scale_initial):
    audio_extradata["scale_initial"] = scale_initial # 0x10000000 is max


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
}


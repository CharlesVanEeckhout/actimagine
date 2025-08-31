
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

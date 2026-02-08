
from .aframe_decoder import AFrameDecoder
from .aframe_encoder import AFrameEncoder


class AFrame:
    def __init__(self, audio_extradata, prev_aframe):
        self.samples = None
        self.pulses = None
        self.scale = None
        self.lpc_filter = None
        self.audio_extradata = audio_extradata
        self.prev_aframe = prev_aframe


    def decode(self, reader):
        self.samples = []
        aframe_decoder = AFrameDecoder(self, reader)
        aframe_decoder.decode()


    def encode(self, writer, goal_samples, strategy):
        self.samples = []
        aframe_encoder = AFrameEncoder(self, writer, goal_samples, strategy)
        aframe_encoder.encode()


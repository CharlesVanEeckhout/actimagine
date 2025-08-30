
from .aframe_decoder import AFrameDecoder

class AFrame:
    def __init__(self, audio_extradata):
        self.samples = None
        self.audio_extradata = audio_extradata


    def decode(self, reader):
        self.samples = []
        aframe_decoder = AFrameDecoder(self, reader)
        aframe_decoder.decode()


    def encode(self, writer):
        pass
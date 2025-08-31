from . import io
from .vframe import VFrame
from .aframe import AFrame


class AVFrame:
    def __init__(self):
        self.data = None

        self.vframe = None
        self.ref_vframes = None
        self.qtab = None

        self.aframes = None
        self.audio_extradata = None


    def set_data(self, data):
        self.data = data


    def init_vframe(self, vframe_width, vframe_height, ref_vframes, qtab):
        self.vframe = VFrame(vframe_width, vframe_height, ref_vframes, qtab)


    def init_aframes(self, qty, audio_extradata, prev_aframe):
        self.aframes = []
        for i in range(qty):
            aframe = AFrame(audio_extradata, prev_aframe)
            self.aframes.append(aframe)
            prev_aframe = aframe


    def decode(self):
        # read bits from little endian uint16 list from msb to lsb
        reader = io.DataReader()
        reader.set_data_bytes([byte for i in range(0, len(self.data)-1, 2) for byte in reversed(self.data[i:i+2])], bitorder="big")
        self.vframe.decode(reader)
        for aframe in self.aframes:
            aframe.decode(reader)


    def encode(self):
        writer = io.BitStreamWriter()
        writer.set_data_bytes(self.data)
        self.vframe.encode(writer)
        for aframe in self.aframes:
            aframe.encode(writer)
        self.data = writer.get_data_bytes()


    def get_audio_samples(self):
        audio_samples = []
        for aframe in self.aframes:
            audio_samples += aframe.samples
        return audio_samples

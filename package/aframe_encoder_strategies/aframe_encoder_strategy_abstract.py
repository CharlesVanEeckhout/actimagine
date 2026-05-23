
from ..aframe import AFrame
from ..aframe_data_handler import AFrameDataHandler


class AFrameEncoderStrategyAbstract:
    def __init__(self):
        if type(self) == AFrameEncoderStrategyAbstract:
            raise TypeError('cannot instantiate abstract class ' + str(type(self)))


    def init_audio_extradata(self, audio_extradata, aframes):
        raise NotImplementedError()


    def encode(self, aframe_encoder):
        raise NotImplementedError()


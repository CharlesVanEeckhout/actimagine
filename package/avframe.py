from . import io


class AVFrame:
    def __init__(self):
        self.data = None
        
        self.vframe = None
        self.ref_avframe_objects = None
        self.qtab = None
        
        self.aframes = None
        self.audio_extradata = None
    
    
    def set_data(self, data):
        self.data = data
    
    
    def init_vframe(self, vframe_width, vframe_height, ref_avframe_objects, qtab):
        self.vframe = VFrame(vframe_width, vframe_height, ref_avframe_objects, qtab)
    
    
    def init_aframes(self, qty, audio_extradata):
        self.aframes = []
        for i in qty:
            self.aframes.append(AFrame())
    
    
    def decode(self):
        reader = io.DataReader()
        self.vframe.decode(reader)
        for aframe in self.aframes:
            aframe.decode(reader)
    
    
    def encode(self):
        writer = io.DataWriter()
        writer.set_data_bytes(self.data)
        self.vframe.encode(writer)
        for aframe in self.aframes:
            aframe.encode(writer)
        self.data = writer.get_data_bytes()

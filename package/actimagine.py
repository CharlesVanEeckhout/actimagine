# code adapted from https://lists.ffmpeg.org/pipermail/ffmpeg-devel/2021-March/277989.html

import numpy as np
import PIL

from .frame_decoder import FrameDecoder
from . import io


quant4x4_tab = [
    [ 0x0A, 0x0D, 0x0A, 0x0D, 0x0D, 0x10, 0x0D, 0x10 ],
    [ 0x0B, 0x0E, 0x0B, 0x0E, 0x0E, 0x12, 0x0E, 0x12 ],
    [ 0x0D, 0x10, 0x0D, 0x10, 0x10, 0x14, 0x10, 0x14 ],
    [ 0x0E, 0x12, 0x0E, 0x12, 0x12, 0x17, 0x12, 0x17 ],
    [ 0x10, 0x14, 0x10, 0x14, 0x14, 0x19, 0x14, 0x19 ],
    [ 0x12, 0x17, 0x12, 0x17, 0x17, 0x1D, 0x17, 0x1D ]
]


class ActImagine:
    def __init__(self):
        pass


    def load_vx(self, data):
        reader = io.BytesReader(data, 0)


        self.file_signature = reader.bytes(4)
        self.frames_qty = reader.int(4)
        self.frame_width = reader.int(4)
        self.frame_height = reader.int(4)
        self.frame_rate = reader.int(4) / 0x10000
        self.quantizer = reader.int(4)
        self.audio_sample_rate = reader.int(4)
        self.audio_streams_qty = reader.int(4)
        self.frame_size_max = reader.int(4)
        self.audio_extradata_offset = reader.int(4)
        self.seek_table_offset = reader.int(4)
        self.seek_table_entries_qty = reader.int(4)

        if (self.frame_width % 16) != 0 or (self.frame_height % 16) != 0:
            raise Exception("frame dimensions " + str(self.frame_width) + "x" + str(self.frame_height) + "px are not multiple of 16x16px")


        self.audio_extradata = {}
        reader_temp = io.BytesReader(data, self.audio_extradata_offset)

        self.audio_extradata["lpc_codebooks"] = []
        for i in range(3):
            self.audio_extradata["lpc_codebooks"].append([])
            for j in range(64):
                self.audio_extradata["lpc_codebooks"][i].append([])
                for k in range(8):
                    self.audio_extradata["lpc_codebooks"][i][j].append(reader_temp.int(2, signed=True))

        self.audio_extradata["scale_modifiers"] = []
        for i in range(8):
            self.audio_extradata["scale_modifiers"].append(reader_temp.int(2))

        self.audio_extradata["lpc_base"] = []
        for i in range(8):
            self.audio_extradata["lpc_base"].append(reader_temp.int(4, signed=True))

        self.audio_extradata["scale_initial"] = reader_temp.int(4)


        self.seek_table = []
        reader_temp = io.BytesReader(data, self.seek_table_offset)
        for i in range(self.seek_table_entries_qty):
            self.seek_table.append({
                "frame_id": reader_temp.int(4),
                "frame_offset": reader_temp.int(4)
            })
        
        
        self.qtab = []
        if self.quantizer < 12 or self.quantizer > 161:
            raise Exception("quantizer " + str(self.quantizer) + " was out of bounds")
        qx = self.quantizer % 6
        qy = self.quantizer // 6
        
        for i in range(2):
            self.qtab.append([])
            for j in range(4):
                self.qtab[i].append(quant4x4_tab[qx][4 * i + j] << qy)
        
        
        self.frame_objects = []
        ref_frame_objects = [None, None, None]
        for i in range(self.frames_qty):
            frame_object = FrameDecoder(self.frame_width, self.frame_height, ref_frame_objects, self.qtab)
            frame_data_size = reader.int(2)
            frame_object.audio_frames_qty = reader.int(2)
            frame_object.data = np.array(list(reader.bytes(frame_data_size-2)), dtype=np.ubyte)
            self.frame_objects.append(frame_object)
            ref_frame_objects = [frame_object] + ref_frame_objects[:-1]


    # generate images and audio from vx data
    def interpret_vx(self):
        self.frame_number = 1
        for frame_object in self.frame_objects:
            frame_object.decode()
            frame_object.export_image("frame{:04d}.png".format(self.frame_number))
            self.frame_number += 1



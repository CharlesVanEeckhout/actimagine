# code adapted from https://lists.ffmpeg.org/pipermail/ffmpeg-devel/2021-March/277989.html

import numpy as np
import wave

from .frame_decoder import FrameDecoder
from . import io


quant4x4_tab = [
    [ 0x0A, 0x0D, 0x10 ],
    [ 0x0B, 0x0E, 0x12 ],
    [ 0x0D, 0x10, 0x14 ],
    [ 0x0E, 0x12, 0x17 ],
    [ 0x10, 0x14, 0x19 ],
    [ 0x12, 0x17, 0x1D ]
]


class ActImagine:
    def __init__(self):
        pass


    def load_vx(self, data):
        reader = io.DataReader()
        reader.set_data_bytes(data)


        self.file_signature = reader.bytes(4)
        self.frames_qty = reader.int_from_bytes(4)
        self.frame_width = reader.int_from_bytes(4)
        self.frame_height = reader.int_from_bytes(4)
        self.frame_rate = reader.int_from_bytes(4) / 0x10000
        self.quantizer = reader.int_from_bytes(4)
        self.audio_sample_rate = reader.int_from_bytes(4)
        self.audio_streams_qty = reader.int_from_bytes(4)
        self.frame_size_max = reader.int_from_bytes(4)
        self.audio_extradata_offset = reader.int_from_bytes(4)
        self.seek_table_offset = reader.int_from_bytes(4)
        self.seek_table_entries_qty = reader.int_from_bytes(4)

        if (self.frame_width % 16) != 0 or (self.frame_height % 16) != 0:
            raise Exception("frame dimensions " + str(self.frame_width) + "x" + str(self.frame_height) + "px are not multiple of 16x16px")


        self.audio_extradata = {}
        reader_temp = io.DataReader()
        reader_temp.set_data_bytes(data[self.audio_extradata_offset:])

        self.audio_extradata["lpc_codebooks"] = []
        for i in range(3):
            self.audio_extradata["lpc_codebooks"].append([])
            for j in range(64):
                self.audio_extradata["lpc_codebooks"][i].append([])
                for k in range(8):
                    self.audio_extradata["lpc_codebooks"][i][j].append(reader_temp.int_from_bytes(2, signed=True))

        self.audio_extradata["scale_modifiers"] = []
        for i in range(8):
            self.audio_extradata["scale_modifiers"].append(reader_temp.int_from_bytes(2))

        self.audio_extradata["lpc_base"] = []
        for i in range(8):
            self.audio_extradata["lpc_base"].append(reader_temp.int_from_bytes(4, signed=True))

        self.audio_extradata["scale_initial"] = reader_temp.int_from_bytes(4)


        self.seek_table = []
        reader_temp = io.DataReader()
        reader_temp.set_data_bytes(data[self.seek_table_offset:])
        for i in range(self.seek_table_entries_qty):
            self.seek_table.append({
                "frame_id": reader_temp.int_from_bytes(4),
                "frame_offset": reader_temp.int_from_bytes(4)
            })


        if self.quantizer < 12 or self.quantizer > 161:
            raise Exception("quantizer " + str(self.quantizer) + " was out of bounds")
        qx = self.quantizer % 6
        qy = self.quantizer // 6
        self.qtab = [i << qy for i in quant4x4_tab[qx]]


        self.frame_objects = []
        ref_frame_objects = [None, None, None]
        for i in range(self.frames_qty):
            frame_object = FrameDecoder(self.frame_width, self.frame_height, ref_frame_objects, self.qtab, self.audio_extradata)
            frame_data_size = reader.int_from_bytes(2)
            frame_object.audio_frames_qty = reader.int_from_bytes(2)
            frame_object.data = np.array(list(reader.bytes(frame_data_size-2)), dtype=np.ubyte)
            self.frame_objects.append(frame_object)
            ref_frame_objects = [frame_object] + ref_frame_objects[:-1]


    # generate images and audio from vx data
    def interpret_vx(self):
        self.frame_number = 1
        audio_samples = np.array([], dtype=np.float32)
        for frame_object in self.frame_objects:
            frame_object.decode()
            frame_object.export_image("frame{:04d}.png".format(self.frame_number))
            audio_s = np.array(frame_object.audio_samples, dtype=np.float32)
            print(frame_object.audio_samples)
            print(audio_s)
            audio_samples = np.concatenate((audio_samples, audio_s), axis=0)
            """with wave.open("frame{:04d}.wav".format(self.frame_number), "w") as f:
                f.setnchannels(1)
                f.setsampwidth(4)
                f.setframerate(self.audio_sample_rate)
                # tobytes has the wrong endianness for a wav file
                f.writeframes(audio_s.tobytes())"""
            self.frame_number += 1
        audio_samples /= np.max(np.abs(audio_samples), axis=0)
        """with wave.open("fullaudio.wav", "w") as f:
            f.setnchannels(1)
            f.setsampwidth(4)
            f.setframerate(self.audio_sample_rate)
            f.writeframes(audio_samples.tobytes())"""



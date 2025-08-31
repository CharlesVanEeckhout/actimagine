# code adapted from https://lists.ffmpeg.org/pipermail/ffmpeg-devel/2021-March/277989.html

import numpy as np
import wave
import logging

from .avframe import AVFrame
from . import io

logger = logging.getLogger(__name__)
logger.propagate = True # enable/disable


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
        self.file_signature = None
        self.frames_qty = None
        self.frame_width = None
        self.frame_height = None
        self.frame_rate = None
        self.quantizer = None
        self.audio_sample_rate = None
        self.audio_streams_qty = None
        self.frame_size_max = None
        self.audio_extradata_offset = None
        self.seek_table_offset = None
        self.seek_table_entries_qty = None
        self.audio_extradata = None
        self.seek_table = None
        self.qtab = None
        self.avframes = None


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
            raise RuntimeError("frame dimensions " + str(self.frame_width) + "x" + str(self.frame_height) + "px are not multiple of 16x16px")


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
            raise RuntimeError("quantizer " + str(self.quantizer) + " was out of bounds")
        qx = self.quantizer % 6
        qy = self.quantizer // 6
        self.qtab = [i << qy for i in quant4x4_tab[qx]]


        self.avframes = []
        ref_vframes = [None, None, None]
        prev_aframe = None
        for i in range(self.frames_qty):
            avframe = AVFrame()
            frame_data_size = reader.int_from_bytes(2)
            aframes_qty = reader.int_from_bytes(2)
            avframe.init_vframe(self.frame_width, self.frame_height, ref_vframes, self.qtab)
            avframe.init_aframes(aframes_qty, self.audio_extradata, prev_aframe)
            avframe.set_data(np.array(list(reader.bytes(frame_data_size-2)), dtype=np.ubyte))
            self.avframes.append(avframe)
            ref_vframes = [avframe.vframe] + ref_vframes[:-1]
            if aframes_qty > 0:
                prev_aframe = avframe.aframes[aframes_qty-1]


    # generate images and audio from vx data
    def interpret_vx(self):
        self.frame_number = 1
        audio_samples = np.array([], dtype=np.float32)
        for avframe in self.avframes:
            avframe.decode()
            avframe.vframe.export_image("frame{:04d}.png".format(self.frame_number))
            logger.debug(avframe.get_audio_samples())
            audio_s = np.array(avframe.get_audio_samples(), dtype=np.float32)
            logger.debug(audio_s)
            audio_samples = np.concatenate((audio_samples, audio_s), axis=0)
            """with wave.open("frame{:04d}.wav".format(self.frame_number), "w") as f:
                f.setnchannels(1)
                f.setsampwidth(4)
                f.setframerate(self.audio_sample_rate)
                # tobytes has the wrong endianness for a wav file
                f.writeframes(audio_s.tobytes())"""
            self.frame_number += 1
        audio_samples /= np.max(np.abs(audio_samples), axis=0)
        with wave.open("fullaudio.wav", "w") as f:
            f.setnchannels(1)
            f.setsampwidth(4)
            f.setframerate(self.audio_sample_rate)
            f.writeframes(audio_samples.tobytes())

# code adapted from https://lists.ffmpeg.org/pipermail/ffmpeg-devel/2021-March/277989.html

import os
import numpy as np
import wave
import json
from PIL import Image
import logging

from .avframe import AVFrame
from .vframe_convert import convert_image_to_frame
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



class ActImagine_LoadVXIterator:
    def __init__(self, avframes):
        self.avframes = avframes.copy()


    def __iter__(self):
        return self


    def __next__(self):
        if len(self.avframes) == 0:
            raise StopIteration
        avframe = self.avframes.pop(0)
        avframe.decode()



class ActImagine_ExportVXFolderIterator:
    def __init__(self, avframes, audio_sample_rate, folder_path):
        self.avframes = avframes.copy()
        self.audio_sample_rate = audio_sample_rate
        self.folder_path = folder_path
        self.audio_samples = np.array([], dtype=np.float32)
        self.frame_number = 1


    def __iter__(self):
        return self


    def __next__(self):
        if len(self.avframes) == 0:
            # todo: when audio decode is complete, remove volume amplify
            self.audio_samples /= np.max(np.abs(self.audio_samples), axis=0)
            with wave.open(os.path.join(self.folder_path, "fullaudio.wav"), "w") as f:
                f.setnchannels(1)
                f.setsampwidth(4)
                f.setframerate(self.audio_sample_rate)
                f.writeframes(self.audio_samples.tobytes())
            raise StopIteration
        avframe = self.avframes.pop(0)
        avframe.vframe.export_image(os.path.join(self.folder_path, f"frame{self.frame_number:04d}.png"))
        logger.debug(avframe.get_audio_samples())
        audio_s = np.array(avframe.get_audio_samples(), dtype=np.float32)
        logger.debug(audio_s)
        self.audio_samples = np.concatenate((self.audio_samples, audio_s), axis=0)
        self.frame_number += 1



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
        self.frame_data_size_max = None
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
        self.frame_data_size_max = reader.int_from_bytes(4)
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
            avframe.set_data(reader.bytes(frame_data_size-2))
            self.avframes.append(avframe)
            ref_vframes = [avframe.vframe] + ref_vframes[:-1]
            if aframes_qty > 0:
                prev_aframe = avframe.aframes[aframes_qty-1]

        return ActImagine_LoadVXIterator(self.avframes)


    def save_vx(self):
        data_audio_extradata = bytearray()
        
        for codebook in self.audio_extradata["lpc_codebooks"]:
            for lpc_filter_part in codebook:
                for value in lpc_filter_part:
                    data_audio_extradata += (value).to_bytes(2, byteorder="little", signed=True)
        
        for scale_modifier in self.audio_extradata["scale_modifiers"]:
            data_audio_extradata += (scale_modifier).to_bytes(2, byteorder="little")
        
        for value in self.audio_extradata["lpc_base"]:
            data_audio_extradata += (value).to_bytes(4, byteorder="little", signed=True)
        
        data_audio_extradata += (self.audio_extradata["scale_initial"]).to_bytes(4, byteorder="little")
        
        data_seek_table = bytearray()
        
        self.seek_table_entries_qty = 0
        for entry in self.seek_table:
            data_seek_table += (entry["frame_id"]).to_bytes(4, byteorder="little")
            data_seek_table += (entry["frame_offset"]).to_bytes(4, byteorder="little")
            self.seek_table_entries_qty += 1
        
        data_avframes = bytearray()
        
        self.frames_qty = 0
        self.frame_data_size_max = 0
        for avframe in self.avframes:
            frame_data_size = len(avframe.data) + 2
            self.frame_data_size_max = max(frame_data_size + 2, self.frame_data_size_max)
            data_avframes += (frame_data_size).to_bytes(2, byteorder="little")
            data_avframes += (len(avframe.aframes)).to_bytes(2, byteorder="little")
            data_avframes += avframe.data
            self.frames_qty += 1
        
        self.audio_extradata_offset = 12*4 + len(data_avframes)
        self.seek_table_offset = 12*4 + len(data_avframes) + len(data_audio_extradata)
        
        data_header = bytearray()
        
        data_header += self.file_signature
        data_header += (self.frames_qty).to_bytes(4, byteorder="little")
        data_header += (self.frame_width).to_bytes(4, byteorder="little")
        data_header += (self.frame_height).to_bytes(4, byteorder="little")
        data_header += (int(self.frame_rate * 0x10000)).to_bytes(4, byteorder="little")
        data_header += (self.quantizer).to_bytes(4, byteorder="little")
        data_header += (self.audio_sample_rate).to_bytes(4, byteorder="little")
        data_header += (self.audio_streams_qty).to_bytes(4, byteorder="little")
        data_header += (self.frame_data_size_max).to_bytes(4, byteorder="little")
        data_header += (self.audio_extradata_offset).to_bytes(4, byteorder="little")
        data_header += (self.seek_table_offset).to_bytes(4, byteorder="little")
        data_header += (self.seek_table_entries_qty).to_bytes(4, byteorder="little")
        
        
        data = data_header + data_avframes + data_audio_extradata + data_seek_table
        
        return data


    def get_properties(self):
        properties = {
            "file_signature": list(self.file_signature),
            "frame_rate": self.frame_rate,
            "quantizer": self.quantizer,
            "audio_sample_rate": self.audio_sample_rate,
            "audio_streams_qty": self.audio_streams_qty,
            "audio_extradata": self.audio_extradata,
            "seek_table": self.seek_table,
        }
        return properties
    

    def set_properties(self, properties):
        self.file_signature = bytearray(properties["file_signature"])
        self.frame_rate = properties["frame_rate"]
        self.quantizer = properties["quantizer"]
        self.audio_sample_rate = properties["audio_sample_rate"]
        self.audio_streams_qty = properties["audio_streams_qty"]
        self.audio_extradata = properties["audio_extradata"]
        self.seek_table = properties["seek_table"]


    def export_vxfolder(self, folder_path):
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        properties = self.get_properties()
        print(properties)
        properties_jsonstr = json.dumps(properties)
        with open(os.path.join(folder_path, "properties.json"), "w") as f:
            f.write(properties_jsonstr)
        return ActImagine_ExportVXFolderIterator(self.avframes, self.audio_sample_rate, folder_path)


    def import_vxfolder(self, folder_path):
        with open(os.path.join(folder_path, "properties.json"), "r") as f:
            properties_jsonstr = f.read()
        properties = json.loads(properties_jsonstr)
        self.set_properties(properties)
        self.audio_streams_qty = 0 # audio is not supported yet
        self.frames_qty = 0
        self.frame_width = None
        self.frame_height = None
        self.avframes = []
        ref_vframes = [None, None, None]
        while True:
            filename = os.path.join(self.folder_path, f"frame{self.frames_qty+1:04d}.png")
            if not os.path.isfile(filename):
                break
            image = Image.open(filename)
            if self.frame_width is None or self.frame_height is None:
                self.frame_width, self.frame_height = image.size
                if (self.frame_width % 16) != 0 or (self.frame_height % 16) != 0:
                    raise RuntimeError("frame dimensions " + str(self.frame_width) + "x" + str(self.frame_height) + "px are not multiple of 16x16px")
            elif (self.frame_width, self.frame_height) != image.size:
                raise RuntimeError(f"dimensions of frame {self.frames_qty+1} ({image.size[0]}x{image.size[1]}px) " + 
                                   f"are not the same as those of the first frame ({self.frame_width}x{self.frame_height}px)")
            avframe = AVFrame()
            avframe.init_vframe(self.frame_width, self.frame_height, ref_vframes, self.qtab)
            avframe.init_aframes(0, self.audio_extradata, None)
            avframe.vframe.plane_buffers = convert_image_to_frame(image)
            ref_vframes = [avframe.vframe] + ref_vframes[:-1]
            self.frames_qty += 1

            

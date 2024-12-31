# code adapted from https://lists.ffmpeg.org/pipermail/ffmpeg-devel/2021-March/277989.html

import argparse
import numpy as np

import read
import vlc

ff_actimagine_vx_residu_mask_new_tab = [
    0x00, 0x08, 0x04, 0x02, 0x01, 0x1F, 0x0F, 0x0A,
    0x05, 0x0C, 0x03, 0x10, 0x0E, 0x0D, 0x0B, 0x07,
    0x09, 0x06, 0x1E, 0x1B, 0x1A, 0x1D, 0x17, 0x15,
    0x18, 0x12, 0x11, 0x1C, 0x14, 0x13, 0x16, 0x19
]

quant4x4_tab = [
    [ 0x0A, 0x0D, 0x0A, 0x0D, 0x0D, 0x10, 0x0D, 0x10 ],
    [ 0x0B, 0x0E, 0x0B, 0x0E, 0x0E, 0x12, 0x0E, 0x12 ],
    [ 0x0D, 0x10, 0x0D, 0x10, 0x10, 0x14, 0x10, 0x14 ],
    [ 0x0E, 0x12, 0x0E, 0x12, 0x12, 0x17, 0x12, 0x17 ],
    [ 0x10, 0x14, 0x10, 0x14, 0x14, 0x19, 0x14, 0x19 ],
    [ 0x12, 0x17, 0x12, 0x17, 0x17, 0x1D, 0x17, 0x1D ]
]


ff_h264_cavlc_coeff_token_table_index = [
    0, 0, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3
]


ff_h264_cavlc_suffix_limit = [
    0, 3, 6, 12, 24, 48, 0x8000
]


"""
        frame_object["audio_frames"] = []
        if frame_object["audio_frames_qty"] > 50:
        print("decoding aborted prematurely: audio_frames_qty is " + str(frame_object["audio_frames_qty"]))
        break
        for j in range(frame_object["audio_frames_qty"]):
        audio_frame_header_word1 = reader.int(2)
        audio_frame_header_word2 = reader.int(2)
        audio_frame_object = {
        "prev_frame_offset": (audio_frame_header_word1 >> 9) & 0x7f,
        "scale_modifier_index": (audio_frame_header_word1 >> 6) & 0x7,
        "pulse_start_position": (audio_frame_header_word2 >> 14) & 0x3,
        "pulse_packing_mode": (audio_frame_header_word2 >> 12) & 0x3,
        "lpc_codebook_indexes": [
        (audio_frame_header_word1 >> 0) & 0x3f,
        (audio_frame_header_word2 >> 6) & 0x3f,
        (audio_frame_header_word2 >> 0) & 0x3f
        ]
        }
        if audio_frame_object["pulse_packing_mode"] == 0:
            audio_frame_object["data"] = reader(2*8)
        elif audio_frame_object["pulse_packing_mode"] == 1:
            audio_frame_object["data"] = reader(2*5)
        elif audio_frame_object["pulse_packing_mode"] == 2:
            audio_frame_object["data"] = reader(2*4)
        elif audio_frame_object["pulse_packing_mode"] == 3:
            audio_frame_object["data"] = reader(2*3)
        frame_object["audio_frames"].append(audio_frame_object)"""


def mid_pred(a, b, c):
    return sorted([a, b, c])[1]


class ActImagine:
    def __init__(self):
        pass


    def load_vx(self, filename):
        with open(filename, "rb") as f:
            data = f.read()

        reader = DataReader(data, 0)


        self.file_signature = reader.bytes(4)
        self.frames_qty = reader.int(4)
        self.frame_width = reader.int(4)
        self.frame_height = reader.int(4)
        self.frame_rate = reader.int(4) / 0x10000
        self.quantiser = reader.int(4)
        self.audio_sample_rate = reader.int(4)
        self.audio_streams_qty = reader.int(4)
        self.frame_size_max = reader.int(4)
        self.audio_extradata_offset = reader.int(4)
        self.seek_table_offset = reader.int(4)
        self.seek_table_entries_qty = reader.int(4)


        self.audio_extradata = {}
        reader_temp = DataReader(data, self.audio_extradata_offset)

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
        reader_temp = DataReader(data, self.seek_table_offset)
        for i in range(self.seek_table_entries_qty):
            self.seek_table.append({
                "frame_id": reader_temp.int(4),
                "frame_offset": reader_temp.int(4)
            })
        
        self.frames = []
        for i in range(self.frames_qty):
            frame_object = {}
            frame_object["size"] = reader.int(2)
            frame_object["audio_frames_qty"] = reader.int(2)
            frame_object["data"] = np.array(list(reader.bytes(frame_object["size"]-2)), dtype=np.ubyte)
            self.frames.append(frame_object)


    def frame_image_getter(self, frame_image, plane, x, y):
        step = 2
        if plane == "y":
            step = 1
        return frame_image[plane][y // step][x // step]

    def frame_image_setter(self, frame_image, plane, x, y, value):
        step = 2
        if plane == "y":
            step = 1
        frame_image[plane][y // step][x // step] = value 

    def frame_image_iterator(self, block, planes, callback, **kwargs):
        for plane in planes:
            step = 2
            if plane == "y":
                step = 1
            for y in range(block["y"], block["y"] + block["h"], step):
                for x in range(block["x"], block["x"] + block["w"], step):
                    callback(x, y, plane, **kwargs)

    def frame_coeff_getter(self, frame_coeff, plane, x, y):
        return self.frame_image_getter(self, frame_coeff, plane, x // 4 + 1, y // 4 + 1)
        
    def frame_coeff_setter(self, frame_coeff, plane, x, y, value):
        self.frame_image_setter(self, frame_coeff, plane, x // 4 + 1, y // 4 + 1, value)


    def predict_inter(self, reader, block, pred_vec, has_delta, ref_frame_image):
        if ref_frame_image is None:
            raise Exception("ref_frame_image was None")
        
        vec = pred_vec.copy()
        if has_delta:
            vec["x"] += reader.signed_expgolomb()
            vec["y"] += reader.signed_expgolomb()
        
        if (
            block["x"] + vec["x"] < 0 or 
            block["x"] + block["w"] + vec["x"] > self.frame_width or
            block["y"] + vec["y"] < 0 or 
            block["y"] + block["h"] + vec["y"] > self.frame_height
        ):
            raise Exception("motion vector moves block out of bounds")
        
        self.vectors[(block["y"] // 16) + 1][(block["x"] // 16) + 1] = vec
        
        def predict_inter_callback(x, y, plane, **kwargs):
            self.frame_image_setter(self.frame_image, plane, x, y, 
                self.frame_image_getter(self.frame_image, plane, x+vec["x"], y+vec["y"])
            )
        
        self.frame_image_iterator(block, "yuv", predict_inter_callback)
        """# luma
        for y in range(block["y"], block["y"] + block["h"]):
            for x in range(block["x"], block["x"] + block["w"]):
                self.frame_image["y"][y][x] = ref_frame_image["y"][y+vec["y"]][x+vec["x"]]
        
        # chroma (uv is per 2x2 px)
        for y in range(block["y"], block["y"] + block["h"], 2):
            for x in range(block["x"], block["x"] + block["w"], 2):
                # u
                self.frame_image["u"][y // 2][x // 2] = ref_frame_image["u"][(y+vec["y"]) // 2][(x+vec["x"]) // 2]
                # v
                self.frame_image["v"][y // 2][x // 2] = ref_frame_image["v"][(y+vec["y"]) // 2][(x+vec["x"]) // 2]"""


    def predict_notile(self, reader, block):
        mode = reader.unsigned_expgolomb()
        print("predict notile " + str(mode))
        if mode == 0:
            raise Exception("unimplemented predict notile uv mode " + str(mode)) # predict_vertical(avctx, x, y, w, h, 0)
        elif mode == 1:
            raise Exception("unimplemented predict notile uv mode " + str(mode)) # predict_horizontal(avctx, x, y, w, h, 0)
        elif mode == 2:
            self.predict_dc(reader, block, "y")
        elif mode == 3:
            raise Exception("unimplemented predict notile uv mode " + str(mode)) # predict_plane(avctx, x, y, w, h, 0, 0)
        else:
            raise Exception("invalid predict notile uv mode " + str(mode))
        self.predict_notile_uv(reader, block)

    def predict_notile_uv(self, reader, block):
        mode = reader.unsigned_expgolomb()
        print("predict notile uv " + str(mode))
        if mode == 0:
            self.predict_dc(reader, block, "u")
            self.predict_dc(reader, block, "v")
        elif mode == 1:
            raise Exception("unimplemented predict notile uv mode " + str(mode)) # predict_horizontal(avctx, x, y, w, h, 0)
        elif mode == 2:
            raise Exception("unimplemented predict notile uv mode " + str(mode)) # predict_vertical(avctx, x, y, w, h, 0)
        elif mode == 3:
            raise Exception("unimplemented predict notile uv mode " + str(mode)) # predict_plane(avctx, x, y, w, h, 0, 0)
        else:
            raise Exception("invalid predict notile uv mode " + str(mode))



    def predict_dc(self, reader, block, plane):
        dc = 128
        if block["x"] != 0 and block["y"] != 0:
            # average of both averages below
            sum_x = block["w"] // 2
            for x in range(block["w"]):
                sum_x += self.frame_image_getter(self.frame_image, plane, block["x"]+x, block["y"]-1)
            
            sum_y = block["h"] // 2
            for y in range(block["h"]):
                sum_y += self.frame_image_getter(self.frame_image, plane, block["x"]-1, block["y"]+y)
            
            dc = ((sum_x // block["w"]) + (sum_y // block["h"])) // 2
            
        elif block["x"] == 0 and block["y"] != 0:
            # average of pixels on the top border of current block
            sum_x = block["w"] // 2
            for x in range(block["w"]):
                sum_x += self.frame_image_getter(self.frame_image, plane, block["x"]+x, block["y"]-1)
            
            dc = sum_x // block["w"]
            
        elif block["x"] != 0 and block["y"] == 0:
            # average of pixels on the left border of current block
            sum_y = block["h"] // 2
            for y in range(block["h"]):
                sum_y += self.frame_image_getter(self.frame_image, plane, block["x"]-1, block["y"]+y)
            
            dc = sum_y // block["h"]
        
        def predict_dc_callback(x, y, plane, **kwargs):
            self.frame_image_setter(self.frame_image, plane, x, y, dc)
        
        self.frame_image_iterator(block, plane, predict_dc_callback)


    def decode_residu_blocks(self, reader, block):
        # residu block is 8x8 px which contains 4 4x4 px blocks for y and 1 8x8 px block for uv
        for y in range(0, block["h"], 8):
            for x in range(0, block["w"], 8):
                residu_mask_tab_index = reader.unsigned_expgolomb()
                if residu_mask_tab_index > 31:
                    raise Exception("invalid residu mask tab index " + str(residu_mask_tab_index))
                residu_mask = ff_actimagine_vx_residu_mask_new_tab[residu_mask_tab_index]
                print("residu block (" + str(x) + ", " + str(y) + ") mask " + "{:05b}".format(residu_mask))
                
                raise Exception("unimplemented decode_residu_blocks")
                
                if residu_mask & 1:
                    nc = None # todo
                    self.decode_residu_cavlc(reader, block["x"]+x, block["y"]+y, nc)
                
                
        raise Exception("unimplemented decode_residu_blocks")

    def decode_residu_cavlc(self, reader, x, y, nc):
        coeff_token = reader.vlc2(FF_H264_CAVLC_COEFF_TOKEN_VLC_BITS, 2)
        raise Exception("unimplemented decode_residu_cavlc")


    def clear_total_coeff(self, block):
        for y in range(0, block["h"], 8):
            for x in range(0, block["w"], 8):
                self.frame_coeff_setter(self.frame_coeffs, "y", block["x"]+x  , block["y"]+y  , 0)
                self.frame_coeff_setter(self.frame_coeffs, "y", block["x"]+x  , block["y"]+y+4, 0)
                self.frame_coeff_setter(self.frame_coeffs, "y", block["x"]+x+4, block["y"]+y  , 0)
                self.frame_coeff_setter(self.frame_coeffs, "y", block["x"]+x+4, block["y"]+y+4, 0)
                self.frame_coeff_setter(self.frame_coeffs, "uv", block["x"]+x, block["y"]+y, 0)


    # generate images and audio from vx data
    def interpret_vx(self):
        self.ref_frame_images = [None, None, None]
        
        self.vectors = []
        for y in range((self.frame_height // 16) + 1):
            self.vectors.append([])
            for x in range((self.frame_height // 16) + 2):
                self.vectors[y].append({"x": 0, "y": 0})
        #vectors_stride = (self.frame_height // 16) + 2
        #vectors_size = ((self.frame_height // 16) + 1) * vectors_stride
        
        self.frame_coeffs = {
            "y": np.zeros((self.frame_height // 4 + 1, self.frame_width // 4 + 1)),
            "uv": np.zeros((self.frame_height // 8 + 1, self.frame_width // 8 + 1)),
        }
        
        for frame_object in self.frames:
            frame_blocks = []
            for y in range(0, self.frame_height, 16):
                for x in range(0, self.frame_width, 16):
                    frame_blocks.append({
                        "x": x,
                        "y": y,
                        "w": 16,
                        "h": 16
                    })
            
            self.frame_image = {
                "y": np.zeros((self.frame_height, self.frame_width)),
                "u": np.zeros((self.frame_height // 2, self.frame_width // 2)),
                "v": np.zeros((self.frame_height // 2, self.frame_width // 2))
            }
            
            # read bits from little endian uint16 list from msb to lsb
            reader = BitsReader(np.unpackbits([byte for i in range(0, len(frame_object["data"])-1, 2) for byte in reversed(frame_object["data"][i:i+2])]), 0)
            
            while len(frame_blocks) > 0:
                block = frame_blocks.pop(0)
                
                self.vectors[(block["y"] // 16) + 1][(block["x"] // 16) + 1] = {"x": 0, "y": 0}
                pred_vec = {
                    "x": mid_pred(
                        self.vectors[(block["y"] // 16) + 1][(block["x"] // 16) + 0]["x"],
                        self.vectors[(block["y"] // 16) + 0][(block["x"] // 16) + 1]["x"],
                        self.vectors[(block["y"] // 16) + 0][(block["x"] // 16) + 2]["x"]
                    ),
                    "y": mid_pred(
                        self.vectors[(block["y"] // 16) + 1][(block["x"] // 16) + 0]["y"],
                        self.vectors[(block["y"] // 16) + 0][(block["x"] // 16) + 1]["y"],
                        self.vectors[(block["y"] // 16) + 0][(block["x"] // 16) + 2]["y"]
                    ),
                }
                
                mode = reader.unsigned_expgolomb()
                print(mode)
                if mode == 0:
                    if block["w"] == 2:
                        raise Exception("cannot v-split block further")
                    frame_blocks = [{
                        "x": block["x"],
                        "y": block["y"],
                        "w": block["w"]//2,
                        "h": block["h"]
                    }, {
                        "x": block["x"] + block["w"]//2,
                        "y": block["y"],
                        "w": block["w"]//2,
                        "h": block["h"]
                    }] + frame_blocks
                    if block["w"] >= 8 and block["h"] >= 8:
                        self.clear_total_coeff(block)
                elif mode == 1:
                    self.predict_inter(reader, block, pred_vec, False, self.ref_frame_images[0])
                    if block["w"] >= 8 and block["h"] >= 8:
                        self.clear_total_coeff(block)
                elif mode == 2:
                    if block["h"] == 2:
                        raise Exception("cannot h-split block further")
                    frame_blocks = [{
                        "x": block["x"],
                        "y": block["y"],
                        "w": block["w"],
                        "h": block["h"]//2
                    }, {
                        "x": block["x"],
                        "y": block["y"] + block["h"]//2,
                        "w": block["w"],
                        "h": block["h"]//2
                    }] + frame_blocks
                    if block["w"] >= 8 and block["h"] >= 8:
                        self.clear_total_coeff(block)
                elif mode == 22:
                    self.predict_notile(reader, block)
                    self.decode_residu_blocks(reader, block)
                elif mode > 23:
                    raise Exception("frame block mode " + str(mode) + " is greater than 23")
                else:
                    raise Exception("unimplemented frame block mode " + str(mode))
            
            self.ref_frame_images = [frame_image] + self.ref_frame_images[:-1]



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    
    
    #print(vlc.run7_vlc.bit_strings)
    """
    actimagine = ActImagine()
    actimagine.load_vx(args.filename)
    actimagine.interpret_vx()"""

if __name__ == "__main__":
    main()



from .frame_includes import *


class KeyframeOnlySimple:
    def __init__(self, frame_encoder):
        self.frame_encoder = frame_encoder


    def predict_dc(self, reader, block, plane):
        dc = 128
        if block["x"] != 0 and block["y"] != 0:
            # average of both averages below
            sum_x = block["w"] // 2
            for x in range(block["w"]):
                sum_x += plane_buffer_getter(self.frame_encoder.actual_plane_buffers, plane, block["x"]+x, block["y"]-1)
            
            sum_y = block["h"] // 2
            for y in range(block["h"]):
                sum_y += plane_buffer_getter(self.frame_encoder.actual_plane_buffers, plane, block["x"]-1, block["y"]+y)
            
            dc = ((sum_x // block["w"]) + (sum_y // block["h"]) + 1) // 2
            
        elif block["x"] == 0 and block["y"] != 0:
            # average of pixels on the top border of current block
            sum_x = block["w"] // 2
            for x in range(block["w"]):
                sum_x += plane_buffer_getter(self.frame_encoder.actual_plane_buffers, plane, block["x"]+x, block["y"]-1)
            
            dc = sum_x // block["w"]
            
        elif block["x"] != 0 and block["y"] == 0:
            # average of pixels on the left border of current block
            sum_y = block["h"] // 2
            for y in range(block["h"]):
                sum_y += plane_buffer_getter(self.frame_encoder.actual_plane_buffers, plane, block["x"]-1, block["y"]+y)
            
            dc = sum_y // block["h"]
        
        def predict_dc_callback(x, y, plane, **kwargs):
            plane_buffer_setter(self.frame_encoder.actual_plane_buffers, plane, x, y, dc)
        
        plane_buffer_iterator(block, plane, predict_dc_callback)


    def predict_notile(self, writer, block):
        writer.unsigned_expgolomb(2) # predict_dc
        self.predict_dc(writer, block, "y")
        
        self.predict_notile_uv(writer, block)

    def predict_notile_uv(self, writer, block):
        writer.unsigned_expgolomb(0) # predict_dc
        self.predict_dc(writer, block, "u")
        self.predict_dc(writer, block, "v")


    def encode_mb(self, writer, block):
        if block["w"] > block["h"]:
            # split the block in left and right parts
            writer.unsigned_expgolomb(0)
            self.encode_mb(writer, block_half_left(block))
            self.encode_mb(writer, block_half_right(block))
            if block["w"] == 8 and block["h"] >= 8:
                self.clear_total_coeff(block)
            return
        
        if block["h"] > 8:
            # split the block in up and down parts
            writer.unsigned_expgolomb(2)
            self.encode_mb(writer, block_half_up(block))
            self.encode_mb(writer, block_half_down(block))
            if block["w"] >= 8 and block["h"] == 8:
                self.clear_total_coeff(block)
            return
        
        # blocks are 8x8 here
        writer.unsigned_expgolomb(22) # predict notile, residu
        self.predict_notile(writer, block)
        self.decode_residu_blocks(writer, block)


    def encode(self):
        writer = self.frame_encoder.writer
        
        for y in range(0, self.frame_encoder.frame_height, 16):
            for x in range(0, self.frame_encoder.frame_width, 16):
                block = {
                    "x": x,
                    "y": y,
                    "w": 16,
                    "h": 16
                }
                
                self.encode_mb(writer, block)


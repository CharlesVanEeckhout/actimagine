import logging

from ... import vlc
from ...frame_includes import *
from ...vframe_decoder import VFrameDecoder

logger = logging.getLogger(__name__)
logger.propagate = True # enable/disable


"""
        self.vframe = None
        self.writer = None
        self.goal_plane_buffers = None
        self.coeff_buffers = None
        self.dct_filters = None"""


def encode_predict_inter(self, block, pred_vec, error_threshold):
    if self.vframe.ref_vframes[0] is None:
        raise RuntimeError("vframe has no ref vframes for encode_predict_inter")
    
    # try with frame 0 first, can use dc
    error_dicts = [block_matching_fourstepsearch(self, self.vframe.ref_vframes[0], block, block_matching_get_error_dc)]
    # the others can't use dc
    if self.vframe.ref_vframes[1] is not None:
        error_dicts.append(block_matching_fourstepsearch(self, self.vframe.ref_vframes[1], block, block_matching_get_error))
        if self.vframe.ref_vframes[2] is not None:
            error_dicts.append(block_matching_fourstepsearch(self, self.vframe.ref_vframes[2], block, block_matching_get_error))
    
    # determine which frame is better
    min_error = 1e1000
    min_i = -1
    for i, error_dict in enumerate(error_dicts):
        if error_dict["min_error"] < min_error:
            min_error = error_dict["min_error"]
            min_i = i
    
    min_error /= block["w"] * block["h"]
    
    if min_error > error_threshold:
        return False
    
    # error is good, lets prepare encoding
    error_dict = error_dicts[min_i]
    
    is_dc = (min_i == 0)
    
    if min_i == 0:
        min_dc = error_dict["min_dc"]
        if min_dc["y"] == 0 and min_dc["u"] == 0 and min_dc["v"] == 0:
            # dont use dc for frame 0
            is_dc = False
    
    delta = {
        "x": error_dict["min_block"]["x"] - block["x"],
        "y": error_dict["min_block"]["y"] - block["y"]
    }
    if not is_dc:
        delta["x"] -= pred_vec["x"]
        delta["y"] -= pred_vec["y"]
    
    has_delta = is_dc or (delta["x"] != 0 or delta["y"] != 0)
    
    # copy ref block to self.vframe
    
    # get residu
    
    has_residu = False
    
    # get mode
    
    """
    mode == 10: # unpredicted delta ref0 + dc offset, residu
    mode == 3: # unpredicted delta ref0 + dc offset, no residu

    mode == 16: # delta, residu, ref 0
    mode == 4: # delta, no residu, ref 0

    mode == 12: # no delta, residu, ref 0
    mode == 1: # no delta, no residu, ref 0


    mode == 17: # delta, residu, ref 1
    mode == 5: # delta, no residu, ref 1

    mode == 20: # no delta, residu, ref 1
    mode == 9: # no delta, no residu, ref 1


    mode == 18: # delta, residu, ref 2
    mode == 6: # delta, no residu, ref 2

    mode == 21: # no delta, residu, ref 2
    mode == 14: # no delta, no residu, ref 2
    """
    mode = -1
    
    # encode
    self.writer.unsigned_expgolomb(mode)
    
    if has_delta:
        self.writer.signed_expgolomb(delta["x"])
        self.writer.signed_expgolomb(delta["y"])
    
    if is_dc:
        self.writer.signed_expgolomb(error_dict["min_dc"]["y"] // 2)
        self.writer.signed_expgolomb(error_dict["min_dc"]["u"] // 2)
        self.writer.signed_expgolomb(error_dict["min_dc"]["v"] // 2)
    
    # encode residu
    
    if has_residu:
        pass
    
    return True



def block_matching_fourstepsearch(self, ref_vframe, block, get_error):
    p = 7
    search_y = []
    for i in range(-(p//2), p//2, 2):
        y = block["y"] + i
        if y < 0 or y >= ref_vframe.height:
            continue
        search_y.append(y)
    search_x = []
    for j in range(-(p//2), p//2, 2):
        x = block["x"] + j
        if x < 0 or x >= ref_vframe.width:
            continue
        search_x.append(x)
    
    center_y = block["y"]
    center_x = block["x"]
    error_dict = {}
    min_error_dict_key = f"{block["x"]},{block["y"]},{block["w"]},{block["h"]}"
    
    while True:
        block_matching_3x3_check(self, ref_vframe, block, error_dict, center_x, center_y, 2)
        if min_error_dict_key == error_dict["min_key"]:
            break
        min_error_dict_key = error_dict["min_key"]
        if error_dict["min_block"]["y"] in search_y:
            center_y = error_dict["min_block"]["y"]
        if error_dict["min_block"]["x"] in search_x:
            center_x = error_dict["min_block"]["x"]
    
    block_matching_3x3_check(self, ref_vframe, block, get_error, error_dict, center_x, center_y, 1)
    return error_dict


def block_matching_3x3_check(self, ref_vframe, block, get_error, error_dict, center_x, center_y, radius):
    for y in range(center_y-radius, center_y+radius+1, radius):
        for x in range(center_x-radius, center_x+radius+1, radius):
            get_error(self, ref_vframe, {"x": x, "y": y, "w": block["w"], h: block["h"]}, error_dict)


def block_matching_get_error(self, ref_vframe, block, error_dict):
    # don't calculate error if block is out-of-bounds
    if block["x"] < 0 or block["x"] + block["w"] >= ref_vframe.width or block["y"] < 0 or block["y"] + block["h"] >= ref_vframe.height:
        return
    
    # don't calculate error if we did so already
    error_dict_key = f"{block["x"]},{block["y"]},{block["w"]},{block["h"]}"
    if error_dict_key in error_dict:
        return
    
    # error must be calculated
    min_error = 1e1000
    if "min_key" in error_dict:
        min_error = error_dict[error_dict["min_key"]]
    
    error = 0
    
    # i will use MSE instead of SAD for error calculation, because it has higher quality according to some papers i found online
    # since all we're looking for is the min error, we can abort early if the error gets larger than min
    for y in range(block["y"], block["y"]+block["h"], 2):
        for x in range(block["x"], block["x"]+block["w"], 2):
            # i could adjust the weights of these diffs, but i think they're already representative of their importance in this colorspace
            diffs = [
                int(self.goal_plane_buffers["y"][y    ][x    ]) - int(ref_vframe.plane_buffers["y"][y    ][x    ]),
                int(self.goal_plane_buffers["y"][y    ][x + 1]) - int(ref_vframe.plane_buffers["y"][y    ][x + 1]),
                int(self.goal_plane_buffers["y"][y + 1][x    ]) - int(ref_vframe.plane_buffers["y"][y + 1][x    ]),
                int(self.goal_plane_buffers["y"][y + 1][x + 1]) - int(ref_vframe.plane_buffers["y"][y + 1][x + 1]),
                int(self.goal_plane_buffers["u"][y // 2][x // 2]) - int(ref_vframe.plane_buffers["u"][y // 2][x // 2]),
                int(self.goal_plane_buffers["v"][y // 2][x // 2]) - int(ref_vframe.plane_buffers["v"][y // 2][x // 2])
            ]
            for diff in diffs:
                error += diff * diff
        if error >= min_error:
            break
    
    error_dict[error_dict_key] = error
    if error < min_error:
        error_dict["min_key"] = error_dict_key
        error_dict["min_error"] = error
        error_dict["min_block"] = block


def block_matching_get_error_dc(self, ref_vframe, block, error_dict):
    # don't calculate error if block is out-of-bounds
    if block["x"] < 0 or block["x"] + block["w"] >= ref_vframe.width or block["y"] < 0 or block["y"] + block["h"] >= ref_vframe.height:
        return
    
    # don't calculate error if we did so already
    error_dict_key = f"{block["x"]},{block["y"]},{block["w"]},{block["h"]}"
    if error_dict_key in error_dict:
        return
    
    # error must be calculated
    # error is relative to dc, so dc comes first
    dc = {
        "y": 0,
        "u": 0,
        "v": 0
    }
    for y in range(block["y"], block["y"]+block["h"], 2):
        for x in range(block["x"], block["x"]+block["w"], 2):
            dc["y"] += int(self.goal_plane_buffers["y"][y    ][x    ]) - int(ref_vframe.plane_buffers["y"][y    ][x    ])
            dc["y"] += int(self.goal_plane_buffers["y"][y    ][x + 1]) - int(ref_vframe.plane_buffers["y"][y    ][x + 1])
            dc["y"] += int(self.goal_plane_buffers["y"][y + 1][x    ]) - int(ref_vframe.plane_buffers["y"][y + 1][x    ])
            dc["y"] += int(self.goal_plane_buffers["y"][y + 1][x + 1]) - int(ref_vframe.plane_buffers["y"][y + 1][x + 1])
            dc["u"] += int(self.goal_plane_buffers["u"][y // 2][x // 2]) - int(ref_vframe.plane_buffers["u"][y // 2][x // 2])
            dc["v"] += int(self.goal_plane_buffers["v"][y // 2][x // 2]) - int(ref_vframe.plane_buffers["v"][y // 2][x // 2])
    # dc values must be even integers
    dc["y"] = round(dc["y"] / block["h"] / block["w"] / 2) * 2
    dc["u"] = round(dc["u"] / (block["h"]/2) / (block["w"]/2) / 2) * 2
    dc["v"] = round(dc["v"] / (block["h"]/2) / (block["w"]/2) / 2) * 2
    
    min_error = 1e1000
    if "min_key" in error_dict:
        min_error = error_dict[error_dict["min_key"]]
    
    error = 0
    
    # i will use MSE instead of SAD for error calculation, because it has higher quality according to some papers i found online
    # since all we're looking for is the min error, we can abort early if the error gets larger than min
    for y in range(block["y"], block["y"]+block["h"], 2):
        for x in range(block["x"], block["x"]+block["w"], 2):
            # i could adjust the weights of these diffs, but i think they're already representative of their importance in this colorspace
            diffs = [
                int(self.goal_plane_buffers["y"][y    ][x    ]) - (int(ref_vframe.plane_buffers["y"][y    ][x    ] + dc["y"])),
                int(self.goal_plane_buffers["y"][y    ][x + 1]) - (int(ref_vframe.plane_buffers["y"][y    ][x + 1] + dc["y"])),
                int(self.goal_plane_buffers["y"][y + 1][x    ]) - (int(ref_vframe.plane_buffers["y"][y + 1][x    ] + dc["y"])),
                int(self.goal_plane_buffers["y"][y + 1][x + 1]) - (int(ref_vframe.plane_buffers["y"][y + 1][x + 1] + dc["y"])),
                int(self.goal_plane_buffers["u"][y // 2][x // 2]) - (int(ref_vframe.plane_buffers["u"][y // 2][x // 2] + dc["u"])),
                int(self.goal_plane_buffers["v"][y // 2][x // 2]) - (int(ref_vframe.plane_buffers["v"][y // 2][x // 2] + dc["v"]))
            ]
            for diff in diffs:
                error += diff * diff
        if error >= min_error:
            break
    
    error_dict[error_dict_key] = error
    if error < min_error:
        error_dict["min_key"] = error_dict_key
        error_dict["min_error"] = error
        error_dict["min_block"] = block
        error_dict["min_dc"] = dc

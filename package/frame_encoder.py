
import numpy as np

from . import io


class FrameEncoder:
    def __init__(self, goal_plane_buffers, ref_frame_objects, qtab):
        self.goal_plane_buffers = goal_plane_buffers
        self.actual_plane_buffers = None
        self.frame_width = goal_plane_buffers["y"].shape[1]
        self.frame_height = goal_plane_buffers["y"].shape[0]
        self.ref_frame_objects = ref_frame_objects
        self.qtab = qtab
        self.audio_frames_qty = None
        self.writer = io.BitsWriter()
        self.strategy = None


    def encode():
        self.strategy.encode(self)

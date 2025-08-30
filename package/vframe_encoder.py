
class VFrameEncoder:
    def __init__(self, vframe, writer, goal_plane_buffers, strategy):
        self.vframe = vframe
        self.writer = writer
        self.goal_plane_buffers = goal_plane_buffers
        self.strategy = strategy


    def encode(self):
        self.strategy.encode(self)

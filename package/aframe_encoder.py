
class AFrameEncoder:
    def __init__(self, aframe, writer, goal_samples, strategy):
        self.aframe = aframe
        self.writer = writer
        self.goal_samples = goal_samples
        self.strategy = strategy


    def encode(self):
        self.strategy.encode(self)

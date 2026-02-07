
from ..aframe import AFrame



class SimplePulseExtend:
    def __init__(self, goal_audio_samples, audio_extradata):
        self.init_goal_audio_samples(goal_audio_samples)
        self.audio_extradata = audio_extradata
        
        self.aframes = [AFrame() for i in self.goal_audio_samples]
        for i in range(1, len(self.aframes)):
            self.aframes[i].prev_aframe = self.aframes[i-1]
        

    def init_goal_audio_samples(self, goal_audio_samples):
        goal_audio_samples = [goal_audio_samples[i:i+128] for i in range(0, len(goal_audio_samples), 128)]
        goal_audio_samples_last = goal_audio_samples[len(goal_audio_samples)-1]
        goal_audio_samples_last += [0] * (128 - len(goal_audio_samples_last))
        self.goal_audio_samples = goal_audio_samples


    def encode(self):
        for aframe, samples in zip(self.aframes, self.goal_audio_samples):
            samples = [samples[3*i] for i in range(42)]
            max_amplitude = 0
            for s in samples:
                max_amplitude = max(max_amplitude, abs(s))
            for i in range(len(samples)):
                samples[i] = min(max(((samples[i] * 4) // max_amplitude) * 2 + 1, -7), 7)
            
            

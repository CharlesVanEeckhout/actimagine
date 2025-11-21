


class SimplePulseExtend:
    def __init__(self, goal_audio_samples, audio_extradata):
        self.init_goal_audio_samples(goal_audio_samples)
        self.audio_extradata = audio_extradata
        
        
        self.aframe_data = []
        for aframe_samples in self.goal_audio_samples:
            
        

    def init_goal_audio_samples(self, goal_audio_samples):
        goal_audio_samples = [goal_audio_samples[i:i+128] for i in range(0, len(goal_audio_samples), 128)]
        goal_audio_samples_last = goal_audio_samples[len(goal_audio_samples)-1]
        goal_audio_samples_last += [0] * (128 - len(goal_audio_samples_last))
        self.goal_audio_samples = goal_audio_samples


    def encode(self):
        pass


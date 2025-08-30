
class VFrame:
    def __init__(self, width, height, ref_avframe_objects, qtab):
        self.width = width
        self.height = height
        self.ref_avframe_objects = ref_avframe_objects
        self.qtab = qtab
        self.plane_buffers = None
    
    
    def decode(self, reader):
        self.plane_buffers = {
            "y": np.zeros((self.frame_height, self.frame_width), dtype=np.uint16),
            "u": np.zeros((self.frame_height // 2, self.frame_width // 2), dtype=np.uint16),
            "v": np.zeros((self.frame_height // 2, self.frame_width // 2), dtype=np.uint16)
        }
        


    def encode(self, writer):
        


    def export_buffers(self, filename):
        for plane in ["y", "u", "v"]:
            with open(f"{filename}_{plane}.bin", "wb") as f:
                for row in self.plane_buffers[plane]:
                    for pixel in row:
                        f.write(pixel.astype(np.uint8))


    def export_image(self, filename):
        test_image = frame_convert.convert_frame_to_image(self.plane_buffers)
        test_image.save(filename)

import argparse
from PIL import Image

from package.actimagine import ActImagine
from package.frame_decoder import FrameDecoder
from package.frame_encoder import FrameEncoder
from package.encoder_strategies.keyframeonly_simple import KeyframeOnlySimple
from package.frame_convert import convert_image_to_frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    
    act = ActImagine()
    with open(args.filename, "rb") as f:
        data = f.read()
    act.load_vx(data)
    #act.interpret_vx()
    
    act.frame_objects[0].decode()
    act.frame_objects[0].export_image("frame_0001.png")
    with Image.open("test.png") as im:
        im_width, im_height = im.size
        plane_buffers = convert_image_to_frame(im)
    frame_encoder = FrameEncoder(plane_buffers, [None, None, None], act.qtab)
    frame_encoder.strategy = KeyframeOnlySimple()
    frame_encoder.encode()
    frame_decoder = FrameDecoder(im_width, im_height, [None, None, None], act.qtab, act.audio_extradata)
    frame_decoder.data = frame_encoder.writer.data
    frame_decoder.audio_frames_qty = 0
    frame_decoder.decode()
    frame_decoder.export_image("frame_0001_codec.png")


if __name__ == "__main__":
    main()


import argparse

from package.actimagine import ActImagine
from package.frame_decoder import FrameDecoder
from package.frame_encoder import FrameEncoder
from package.encoder_strategies.keyframeonly_simple import KeyframeOnlySimple


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
    frame_encoder = FrameEncoder(act.frame_objects[0].plane_buffers, [None, None, None], act.qtab)
    frame_encoder.strategy = KeyframeOnlySimple()
    frame_encoder.encode()
    frame_decoder = FrameDecoder(act.frame_width, act.frame_height, [None, None, None], act.qtab, act.audio_extradata)
    frame_decoder.data = frame_encoder.writer.data
    frame_decoder.decode()
    frame_decoder.export_image("frame_0001_codec.png")


if __name__ == "__main__":
    main()


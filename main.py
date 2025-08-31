import argparse
from PIL import Image
import logging

from package.actimagine import ActImagine
from package.vframe import VFrame
import package.io as io
from package.vframe_encoder_strategies.keyframeonly_simple import KeyframeOnlySimple
from package.vframe_convert import convert_image_to_frame


def main():
    logging.basicConfig(filename='main.log', level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()

    act = ActImagine()
    with open(args.filename, "rb") as f:
        data = f.read()
    act.load_vx(data)
    act.interpret_vx()

    """act.avframes[0].decode()
    act.avframes[0].vframe.export_image("frame_0001.png")
    with Image.open("frame_0001.png") as im:
        im_width, im_height = im.size
        plane_buffers = convert_image_to_frame(im)
    vframe = VFrame(im_width, im_height, [None, None, None], act.qtab)
    writer = io.BitStreamWriter()
    vframe.encode(writer, plane_buffers, KeyframeOnlySimple())
    reader = io.DataReader()
    data_bytes = writer.get_data_bytes()
    reader.set_data_bytes([byte for i in range(0, len(data_bytes)-1, 2) for byte in reversed(data_bytes[i:i+2])], bitorder="big")
    vframe.decode(reader)
    vframe.export_image("frame_0001_codec.png")"""


if __name__ == "__main__":
    main()


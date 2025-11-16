import argparse
from PIL import Image
import logging

from package.actimagine import ActImagine
from package.vframe import VFrame
import package.io as io
from package.vframe_encoder_strategies import KeyframeOnlySimple
from package.vframe_convert import convert_image_to_frame


def load_vx_and_export_vxfolder(args):
    act = ActImagine()
    with open(args.filename, "rb") as f:
        data = f.read()
    load_vx_iter = act.load_vx(data)
    for i, _ in enumerate(load_vx_iter):
        print(f"loading vx file: frame {i+1}/{act.frames_qty}")
    print("loading vx file: complete")
    export_vx_iter = act.export_vxfolder("vx_folder")
    for i, _ in enumerate(export_vx_iter):
        print(f"exporting vx folder: frame {i+1}/{act.frames_qty}")
    print("exporting vx folder: complete")


def import_vxfolder_and_save_vx(args):
    act = ActImagine()
    print("importing vx folder: start")
    import_vxfolder_iter = act.import_vxfolder("vx_folder")
    for i, _ in enumerate(import_vxfolder_iter):
        print(f"importing vx folder: frame {i+1}/???")
    print("importing vx folder: complete")
    vframe_strategy = KeyframeOnlySimple()
    for i, avframe in enumerate(act.avframes):
        avframe.encode(avframe.vframe.plane_buffers, vframe_strategy)
        print(f"encoding vx folder: frame {i+1}/{act.frames_qty}")
    print("encoding vx folder: complete")
    data_new = act.save_vx()
    with open(args.filename+"new", "wb") as f:
        f.write(bytes(data_new))
    


def load_vx_and_save_vx(args):
    act = ActImagine()
    with open(args.filename, "rb") as f:
        data = f.read()
    act.load_vx(data)
    data_new = act.save_vx()
    with open(args.filename+"new", "wb") as f:
        f.write(bytes(data_new))


def reencode_first_frame(args):
    act = ActImagine()
    with open(args.filename, "rb") as f:
        data = f.read()
    load_vx_iter = act.load_vx(data)
    next(load_vx_iter)
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
    vframe.export_image("frame_0001_codec.png")


def main():
    logging.basicConfig(filename='main.log', level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()

    load_vx_and_export_vxfolder(args)


if __name__ == "__main__":
    main()


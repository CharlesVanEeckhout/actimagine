import numpy as np
from scipy.io import wavfile
import os
import subprocess

from package.actimagine import ActImagine
from package.avframe import AVFrame
from package import io
from package.vframe_encoder_strategies import SimpleKeyframeOnly
from tests.lpc_test_context import lpc_test_context
from tests import lpc_test


FOLDER_FFMPEG = "../ffmpeg vx"
FOLDER_FFMPEG_CMD = "../ffmpeg\\ vx"
FILENAME_VXNEW = "./mov00.vxnew"
FILENAME_EXPECTED = "./tests/lpc_test_expected.py"


def run_or_exit(args, err):
    completed_process = subprocess.run(args, shell=True)
    if completed_process.returncode != 0:
        print("\n" + err + "\n")
        exit(completed_process.returncode)


def get_ff_data(callback_context_tweaker):
    # get aframe data
    audio_extradata = lpc_test.get_default_audio_extradata()
    aframe_data_handlers = callback_context_tweaker(lpc_test.get_default_aframe_data_handler, audio_extradata)

    act = ActImagine()
    act.set_properties({
        "file_signature": b'VXDS',
        "frame_rate": 128 * 0x10000 / 0x10000,
        "quantizer": 32,
        "audio_sample_rate": 128 * 128,
        "audio_streams_qty": 1,
        "audio_extradata": audio_extradata,
        "seek_table": [{
                "frame_id": 0,
                "frame_offset": 0x30 # address of frame 0 (always after actimagine header)
            }],
    })
    act.frame_width = 32
    act.frame_height = 32

    avframe = AVFrame()
    avframe.aframes = [None]*len(aframe_data_handlers) # so that len(avframe.aframes) is correct
    act.avframes = [avframe]
    # generate vframe data
    avframe.init_vframe(act.frame_width, act.frame_height, None, act.qtab)
    vframe = avframe.vframe
    writer = io.BitStreamWriter()
    goal_plane_buffers = {
        "y": np.zeros((vframe.height, vframe.width), dtype=np.uint16),
        "u": np.zeros((vframe.height // 2, vframe.width // 2), dtype=np.uint16),
        "v": np.zeros((vframe.height // 2, vframe.width // 2), dtype=np.uint16)
    }
    vframe.encode(writer, goal_plane_buffers, SimpleKeyframeOnly())
    # append aframe data
    for aframe_data_handler in aframe_data_handlers:
        aframe_data_handler.pack_to_writer(writer)

    avframe.data = writer.get_data_bytes()

    # save vxnew
    data_new = act.save_vx()
    with open(FILENAME_VXNEW, "wb") as f:
        f.write(bytes(data_new))

    # load vxnew with ffmpeg
    run_or_exit(f"{FOLDER_FFMPEG_CMD}/ffmpeg -i {FILENAME_VXNEW} -c:v png -c:a pcm_s16le {FOLDER_FFMPEG_CMD}/mov00_%04d.png {FOLDER_FFMPEG_CMD}/mov00_audio.wav", "error")

    ff_samplerate, ff_data = wavfile.read(f"{FOLDER_FFMPEG}/mov00_audio.wav")
    os.remove(f"{FOLDER_FFMPEG}/mov00_audio.wav")

    return list(ff_data)


def main():
    file_content = "lpc_test_expected = {\n"
    for k, v in lpc_test_context.items():
        file_content += f"    '{k}': [\n"
        for callback_context_tweaker in v:
            ff_data = get_ff_data(callback_context_tweaker)
            file_content += f"        {ff_data},\n"
        file_content += "    ],\n"
    file_content += "}\n"

    with open(FILENAME_EXPECTED, "w") as f:
        f.write(file_content)


if __name__ == "__main__":
    main()


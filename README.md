# ActImagine Video Codec Python Library

This is a Python library for decoding and encoding ActImagine video files (.vx).
It is made specifically for the version of ActImagine used in Mega Man ZX, so compatibility with other files is not guaranteed.


## Files

package/ - This is the library. You can import this folder into your projects as you would for any other Python package.

main.py - Contains examples of potential usages of the library.

test.py - Run unit tests on certain functionalities of the library.


## API Documentation

### package.actimagine.ActImagine

ActImagine video file.


**`load_vx(data)`**

Given the data bytes of an ActImagine video file, it will load the file's header into the ActImagine object's attributes.
This will also return an iterator to decode each audiovisual frame.


**`save_vx()`**

Convert the contents of the ActImagine object into data bytes of an ActImagine video file.
Those data bytes are returned by the function.


**`export_vxfolder(folder_path)`**

Export the contents of the ActImagine object as a folder containing video frames as a sequence of PNG files, audio as a WAV file and extra information as a JSON file.
This folder will be created at the path specified by the `folder_path` argument.
Returns an iterator to export each video frame.


**`import_vxfolder(folder_path)`**

Import the contents of the folder at the path specified by the `folder_path` argument into the ActImagine object.
Returns an iterator to import each video frame.


### package.avframe.AVFrame

Audiovisual frame in the video file.


**`encode(goal_plane_buffers, vframe_strategy, aframe_strategy)`**

Given plane buffers of the image to encode and a video encoding strategy, this will encode the video aspect of the audiovisual frame.
It will also encode the samples in each AFrame of the AVFrame using the audio encoding strategy.


### package.avframe.VFrame

Visual component of an audiovisual frame.


### package.avframe.AFrame

Audio component of an audiovisual frame. Each AFrame is 128 samples, so there are many of them in an audiovisual frame.


### package.vframe_convert

Utilities to convert images to plane buffers and vice-versa.


**`convert_image_to_frame(image)`**

Converts a [Pillow Image object](https://pillow.readthedocs.io/en/stable/reference/Image.html) into plane buffers.


**`convert_frame_to_image(frame)`**

Converts plane buffers into a Pillow Image object.


### package.vframe_encoder_strategies.SimpleKeyframeOnly

The first video encoding strategy made for this library. Uses very few features of the codec.


### package.aframe_encoder_strategies.SimplePulseExtend

The first audio encoding strategy made for this library. In an aframe, each third sample is used directly as a pulse and is extended over three samples for effective 2-bit per sample sound. 8 levels of volume (+silence) per aframe.


**`init_audio_extradata(audio_extradata)`**

Initializes the audio_extradata of the ActImagine object. You need to do this before encoding audio.


### Anything else

Anything else is internal to the library, so use at your own peril.


## Known Issues

- The audio decoding is incomplete. Please don't use this library to extract audio yet. I would appreciate any help in understanding audio decoding.

- Despite the incomplete audio decoding, I could create a basic audio encoding strategy. The audio produced by this strategy is of low quality and mono only. More investigation of audio decoding is required before better strategies can be added.

- The current video encoding strategy produces an output that is large in filesize and laggy to play back on the DS. Video encoding strategies will be added that will be more efficient on those fronts.


## References

Thanks to Gericom on gbadev Discord for creating the original ActImagine video file decoder for ffmpeg. I found the patch to be most compatible with ffmpeg n4.5-dev, but you'll need to make adjustments. https://lists.ffmpeg.org/pipermail/ffmpeg-devel/2021-March/277989.html

Multimedia Wiki Article. https://wiki.multimedia.cx/index.php/Actimagine_Video_Codec

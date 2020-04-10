"""Video output tools for turnovertools."""

import ffmpeg
from timecode import Timecode

class VideoFile(object):
    """A videofile which can either be imported or exported from."""
    def __init__(self, filepath, **kwargs):
        self.filepath = filepath
        self._probe()

    def _probe(self):
        probe = ffmpeg.probe(self.filepath)
        vid_stream = next(stream for stream in probe['streams'] if
                          stream['codec_type'] == 'video')
        self.framerate = vid_stream['r_frame_rate']
        self.duration = Timecode(self.framerate,
                                 start_seconds=float(probe['format']
                                                     ['duration']))
        if 'timecode' in probe['format']['tags']:
            self.src_start_tc = Timecode(
                self.framerate, probe['format']['tags']['timecode'])
        else:
            self.src_start_tc = Timecode(clip.framerate, '00:00:00:00')
            self.src_end_tc = clip.src_start_tc + clip.duration
        width = vid_stream['width']
        height = vid_stream['height']
        self.scale = (int(width), int(height))
        aw, ah = vid_stream['display_aspect_ratio'].split(':')
        self.aspect_ratio = float(aw) / float(ah)
        self.bitrate = int(probe['format']['bit_rate'])

    def stream_frames(self, frames):
        for frame in frames:
            if not isinstance(frame, Timecode):
                frame = Timecode(self.framerate, frame)
            job = JPEG(
                self.get_ffmpeg_input(self.ss_at(frame),
                                      self.frames_to_seconds(1))).output()
            yield capture_out(job)

    def get_ffmpeg_input(self, ss=None, t=None, **kwargs):
        kwargs = dict()
        if ss is not None:
            kwargs['ss'] = ss
        if t is not None:
            kwargs['t'] = t
        return ffmpeg.input(self.filepath, **kwargs)

    def ss_at(self, tc):
        return range_to_real_offset(self.src_start_tc, tc,
                                    self.framerate)
    
    def frames_to_seconds(self, frames):
        return frames / framerate_to_float(self.framerate)


class OutputPreset(object):
    kwargs = {}

    def __init__(self, input, filepath='pipe:', **kwargs):
        self.input = input
        self.filepath = filepath

    def output(self):
        return self.input.output(self.filepath, **self.kwargs)

class JPEG(OutputPreset):
    kwargs = {'format': 'image2pipe', 'vcodec': 'mjpeg', 'q':1, 'vsync':0}

def range_to_real_offset(start_tc, end_tc, framerate):
    frames = (end_tc - start_tc).frames
    framerate = framerate_to_float(framerate)
    return frames / framerate

def framerate_to_float(framerate):
    try:
        framerate = float(framerate)
    except ValueError:
        dividend, divisor = framerate.split('/')
        framerate = int(dividend) / int(divisor)
    else:
        if framerate == 23.98:
            framerate = 23.976
    return framerate

def capture_out(stream):
    vid, _ = ffmpeg.run(stream, capture_stdout=True, capture_stderr=False)
    return vid

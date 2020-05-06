"""Child class of SourceClip describing actual mediafiles."""

import json
import os
import subprocess

from turnovertools.mediaobjects import SourceClip, Timecode

def get_media_stream(streams):
    """Returns the metadata for the media stream in an MXF file,
    discarding data streams."""
    found = None
    for stream in streams:
        # skip 'data' streams that provide info about related mxf files
        if stream['codec_type'] == 'data':
            continue
        if found:
            raise UserWarning('Expected only one media stream per MXF.')
        found = stream
    return found

def stream_jpeg(stream):
    """Given a jpeg image string, yield individual jpegs."""
    buffer = []
    for chunk in stream:
        buffer.append(chunk)
        if chunk == 0xd9 and buffer[-2] == 0xff:
            yield bytes(buffer)
            buffer = []


class MediaFile(SourceClip):
    """A SourceClip that describes an actual mediafile. Includes video
    input and output, as well as generating metadata from ffprobe."""

    def __init__(self, mediatype=None, pix_fmt=None, seconds=None,
                 track_name=None, file_package_umid=None, reel_umid=None,
                 material_package_umid=None, format_name=None,
                 bitrate=None, size=None, filepath=None, poster_frame=None,
                 **kwargs):
        super(MediaFile, self).__init__(**kwargs)
        self.mediatype = mediatype
        self.pix_fmt = pix_fmt
        self.seconds = seconds
        self.file_package_umid = file_package_umid
        self.reel_umid = reel_umid
        self.material_package_umid = material_package_umid
        self.umid = self._choose_umid()
        self.track_name = track_name
        self.format_name = format_name
        self.bitrate = int(bitrate)
        self.size = int(size)
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self._poster_frame = Timecode(self.src_framerate, poster_frame)

    def _choose_umid(self):
        if self.file_package_umid:
            return self.file_package_umid
        if self.reel_umid:
            return self.reel_umid
        return self.material_package_umid

    @property
    def poster_frame(self):
        return self._poster_frame

    @poster_frame.setter
    def poster_frame(self, val):
        if val is not None:
            val = Timecode(self.src_framerate, val)
        self._poster_frame = val

    def thumbnail(self, ss=None, interval=50, scale=(320, 180)):
        """Return a single thumbnail for the video, chosen from roughly
        the middle of the clip."""
        if self.poster_frame is not None:
            interval = 1
            if hasattr(self.poster_frame, 'framerate'):
                ss = self.poster_frame.real_seconds(self.src_start_tc)
            else:
                ss = self.poster_frame / self.src_start_tc.f_framerate
        if ss is None:
            interval_seconds = interval / float(self.src_framerate)
            if self.seconds > interval_seconds:
                ss = self.seconds / 2 - interval_seconds / 2
            else:
                ss = self.seconds / 2
                interval = round(self.seconds * float(self.src_framerate))
        return next(self.thumbnails(frames=1, ss=ss, interval=interval, scale=scale))

    def thumbnails(self, frames=None, ss=None, interval=100, scale=(320, 180)):
        """Yield thumbnails for the video, chosen at a given interval."""
        filters = f'scale={scale[0]}:{scale[1]}'
        if interval > 1:
            filters += f',thumbnail={interval}'
        args = ['ffmpeg']
        if ss:
            args.extend(('-ss', str(ss)))
        args.extend(('-i', self.filepath, '-vcodec', 'mjpeg', '-vf',
                     filters))
        if frames is not None:
            args.extend(('-vframes', str(frames)))
        args.extend(('-f', 'image2pipe', '-'))
        ffmpeg = subprocess.run(args, capture_output=True, check=True)
        yield from stream_jpeg(ffmpeg.stdout)

    @classmethod
    def probe(cls, filepath):
        """Creates a MediaFile object by probing a videofile."""
        args = ['ffprobe', '-of', 'json', '-show_format', '-show_streams', filepath]
        probe = subprocess.run(args, capture_output=True, check=False)
        data = json.loads(probe.stdout.decode('utf8'))
        mformat = data['format']
        tags = mformat['tags']
        stream = get_media_stream(data['streams'])
        stream_tags = stream['tags']


        # calculate src_end_timecode based on framerate and seconds
        framerate = stream.get('r_frame_rate')
        seconds = float(stream.get('duration'))
        src_start_tc = Timecode(framerate,
                                stream_tags.get('timecode', '00:00:00:00'))
        try:
            framerate = float(framerate)
        except ValueError:
            fraction = framerate.split('/')
            framerate = float(fraction[0]) / float(fraction[1])
        src_end_tc = src_start_tc + round(seconds*framerate)

        # guess source_file vs tape
        reel = stream_tags.get('reel_name')
        tape = None
        source_file = None
        if reel and '.' in reel:
            source_file = reel
        else:
            tape = reel

        return MediaFile(mediatype=stream.get('codec_type'),
                         clip_name=tags.get('material_package_name'),
                         pix_fmt=stream.get('pix_fmt'),
                         source_size=(stream.get('width'), stream.get('height')),
                         seconds=seconds,
                         src_start_tc=src_start_tc,
                         src_end_tc=src_end_tc,
                         file_package_umid=stream_tags.get('file_package_umid').lower(),
                         reel_umid=stream_tags.get('reel_umid').lower(),
                         material_package_umid=tags.get('material_package_umid').lower(),
                         track_name=stream_tags.get('track_name'),
                         format_name=mformat.get('format_name'),
                         bitrate=mformat.get('bit_rate'),
                         size=mformat.get('size'),
                         filepath=filepath,
                         source_file=source_file,
                         tape=tape)

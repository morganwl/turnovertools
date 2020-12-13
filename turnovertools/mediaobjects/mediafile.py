"""Child class of SourceClip describing actual mediafiles."""

import json
import os
import subprocess

from turnovertools.mediaobjects import SourceClip, Timecode

FFMPEG = '/usr/local/bin/ffmpeg'
FFPROBE = '/usr/local/bin/ffprobe'
FFPLAY = '/usr/local/bin/ffplay'

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
    if buffer:
        msg = f'Unexpected data %{len(buffer)} bytes, ending with {buffer[:-2]}.'
        raise ValueError(msg)


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
        if poster_frame:
            poster_frame = Timecode(self.src_framerate, poster_frame)
        self._poster_frame = poster_frame

    def _choose_umid(self):
        if self.file_package_umid:
            return self.file_package_umid
        if self.reel_umid:
            return self.reel_umid
        return self.material_package_umid

    @property
    def poster_frame(self):
        """If set, poster_frame will be used for thumbnail method."""
        return self._poster_frame

    @poster_frame.setter
    def poster_frame(self, val):
        """Sets poster_frame as a Timecode object matching the src_framerate.
        Also accepts a Timecode object."""
        if isinstance(val, int):
            val = self.src_start_tc + val
        elif val is not None:
            val = Timecode(self.src_framerate, val)
        self._poster_frame = val

    def play(self, start_tc=None, end_tc=None):
        """Executes an ffplay process, using marked tc if none is provided."""
        if start_tc is not None:
            start_tc = Timecode(self.src_framerate, start_tc)
        if end_tc is not None:
            end_tc = Timecode(self.src_framerate, end_tc)
        start_tc = start_tc or self.mark_start_tc or self.src_start_tc
        end_tc = end_tc or self.mark_end_tc or self.src_end_tc
        start_second = str((start_tc - self.src_start_tc).frames / self.src_start_tc.f_framerate)
        real_duration = str((end_tc - start_tc - 1).frames / end_tc.f_framerate)
        subprocess.run((FFPLAY, '-ss', start_second, '-t',
                        real_duration, self.filepath),
                       capture_output=True)

    def thumbnail(self, start_second=None, interval=50, scale=(320, 180)):
        """Return a single thumbnail for the video, chosen from roughly
        the middle of the clip."""
        if self.poster_frame is not None:
            interval = 1
            start_second = self.poster_frame.real_seconds(self.src_start_tc)
        # if no start_second is specified, choose from middle of marked region
        if start_second is None:
            if interval < self.mark_duration.frames:
                start_offset = round(self.mark_duration.frames / 2 - interval / 2)
                start_tc = (self.mark_start_tc or self.src_start_tc) + start_offset
            else:
                start_tc = (self.mark_start_tc or self.src_start_tc)
                interval = self.mark_duration.frames
            start_second = self.real_seconds(start_tc)
        # return the thumbnail, raising an exception if necessary
        try:
            return next(self.thumbnails(frames=1, start_second=start_second,
                                        interval=interval, scale=scale))
        except StopIteration as err:
            msg = f'No image yielded at {start_second} with interval {interval}.'
            raise Exception(msg) from err

    def thumbnails(self, frames=None, start_second=None,
                   interval=100, scale=(320, 180)):
        """Yield thumbnails for the video, chosen at a given interval."""
        filters = f'scale={scale[0]}:{scale[1]}'
        if interval > 1:
            filters += f',thumbnail={interval}'
        args = [FFMPEG]
        if start_second:
            args.extend(('-ss', str(start_second)))
        args.extend(('-i', self.filepath, '-vcodec', 'mjpeg', '-vf',
                     filters))
        if frames is not None:
            args.extend(('-vframes', str(frames)))
        args.extend(('-f', 'image2pipe', '-'))
        ffmpeg = subprocess.run(args, capture_output=True, check=True)
        yield from stream_jpeg(ffmpeg.stdout)

    # pylint: disable=R0914
    @classmethod
    def probe(cls, filepath):
        """Creates a MediaFile object by probing a videofile."""
        args = [FFPROBE, '-of', 'json', '-show_format', '-show_streams', filepath]
        probe = subprocess.run(args, capture_output=True, check=False)
        data = json.loads(probe.stdout.decode('utf8'))
        mformat = data['format']
        tags = mformat['tags']
        stream = get_media_stream(data['streams'])
        stream_tags = stream['tags']

        # calculate src_end_timecode based on framerate and seconds
        framerate = stream.get('r_frame_rate')
        seconds = float(stream.get('duration'))
        timecode = (stream_tags.get('timecode') or tags.get('timecode') or
                    '00:00:00:00')
        src_start_tc = Timecode(framerate, timecode)
        try:
            framerate = float(framerate)
        except ValueError:
            fraction = framerate.split('/')
            framerate = float(fraction[0]) / float(fraction[1])
        src_end_tc = src_start_tc + round(seconds*framerate)
        src_end_tc.f_framerate = src_start_tc.f_framerate

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
                         src_framerate=framerate,
                         src_start_tc=str(src_start_tc),
                         src_end_tc=str(src_end_tc),
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

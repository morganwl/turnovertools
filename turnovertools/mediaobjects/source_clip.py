"""SourceClip class, a general purpose object for media sources."""

import dateutil.parser
import datetime
import os

import turnovertools.mediaobjects as mobs
from turnovertools.mediaobjects import Timecode

class SourceClip(mobs.Clip):
    """General purpose object for source clips and their metadata."""

    _provides_attrs = ['umid', 'tracks', 'source_path', 'source_size',
                       'source_codec', 'sensor_framerate', 'shoot_date',
                       'mark_start_tc', 'mark_end_tc']

    def __init__(self, *args, umid=None, tracks=None, source_path=None,
                 source_size=None, source_codec=None, sensor_framerate=None,
                 shoot_date=None, mark_start_tc=None, mark_end_tc=None,
                 **kwargs):
        super(SourceClip, self).__init__(*args, **kwargs)

        if mark_start_tc:
            mark_start_tc = Timecode(self.src_framerate, mark_start_tc)
        if mark_end_tc:
            mark_end_tc = Timecode(self.src_framerate, mark_end_tc)

        self.umid = umid
        self.tracks = tracks
        self.source_path = source_path
        self.source_size = source_size
        self.source_codec = source_codec
        self.sensor_framerate = sensor_framerate
        if shoot_date and isinstance(shoot_date, str):
            shoot_date = dateutil.parser.parse(shoot_date)
        self.shoot_date = shoot_date
        self.mark_start_tc = mark_start_tc
        self.mark_end_tc = mark_end_tc

    @property
    def mark_duration(self):
        """Returns the duration between mark_start_tc and mark_end_tc,
        using src_in and src_out respectively if marks are not defined."""
        mark_in = self.mark_start_tc or self.src_start_tc
        mark_out = self.mark_end_tc or self.src_end_tc
        return mark_out - mark_in

    @classmethod
    def dummy(cls, **kwargs):
        """Creates a dummy object with generic, properly formed values."""
        defaults = dict(umid=('0x060a2b340101010501010f101300000' +
                              '0038ca92d8957a205dc34685b35a9e1ce'),
                        tracks='VA1A2A3A4',
                        source_path=os.path.join('/', 'Volumes', 'Drive',
                                                 'slug.mov'),
                        source_size=(4096, 1716),
                        source_codec='ProRes 4444 (4096p)',
                        sensor_framerate='60',
                        shoot_date=datetime.date(2020, 4, 23),
                        mark_start_tc='01:01:02:00',
                        mark_end_tc='01:01:03:12')
        defaults.update(kwargs)
        return super().dummy(**defaults)

    @classmethod
    def standard_attrs(cls):
        """Returns a list of all the attributes this media object is
        expected to provide, and will set from kwargs on input."""
        return SourceClip._provides_attrs + super().standard_attrs()

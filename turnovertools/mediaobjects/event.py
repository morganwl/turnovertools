"""Event class, a general purpose object for events in edit sequences."""

from warnings import warn

from . import Timecode
from turnovertools.mediaobjects import Mob, Clip


class Event(Clip):
    """Generic event in an edit sequence, references a source clip via tape
    or source_file attribute, which are elided into the reel property."""

    _provides_attrs = ['num', 'tr_code', 'aux', 'rec_framerate',
                       'rec_start_tc', 'rec_end_tc', 'track']

    # pylint: disable=too-many-instance-attributes
    # pylint: disable-msg=too-many-locals
    # pylint: disable-msg=too-many-arguments
    #
    # we need as many attributes as the object spec requires. consider finding
    # logical subgroupings of attributes.
    def __init__(self, num=None, tr_code=None, aux=None,
                 rec_framerate=None, rec_start_tc=None, rec_end_tc=None,
                 track=None, **kwargs):
        super(Event, self).__init__(**kwargs)

        self.num = num
        self.tr_code = tr_code
        self.aux = aux
        self.rec_framerate = self._parse_framerate(rec_framerate,
                                                   rec_start_tc,
                                                   rec_end_tc)
        self.rec_start_tc = Timecode(self.rec_framerate, rec_start_tc)
        self.rec_end_tc = Timecode(self.rec_framerate, rec_end_tc)
        self.track = track

    @property
    def rec_duration(self):
        """Returns difference of rec_end_tc and rec_start_tc. Timecode durations
        are inclusive, eg 00:00:01:00 + 00:00:01:23 = 00:00:02:00, because
        00:00:00:23 == 24 frames."""
        return self.rec_end_tc - self.rec_start_tc

    @classmethod
    def dummy(cls, **kwargs):
        """Creates a dummy object with generic, properly formed values."""
        defaults = dict(num='1',
                        tr_code='V',
                        aux='C',
                        rec_framerate='24',
                        rec_start_tc='01:00:00:00',
                        rec_end_tc='01:00:10:00',
                        track=1)
        defaults.update(kwargs)
        return super().dummy(**defaults)

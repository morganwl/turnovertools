"""Parent object for media object classes."""

from warnings import warn

from turnovertools.mediaobjects import Timecode

def conflicting_values(values):
    """Returns True if iterable values contain more than one unique,
    non-None value, or no non-None values."""
    unique_values = dict.fromkeys(values, 1)
    unique_values = tuple(filter(None, unique_values))
    return len(unique_values) != 1

class Mob:
    """Parent object for media object classes, providing common methods
    for working with media objects."""

    _provides_attrs = []

    def __init__(self, keep_customs=True, **kwargs):
        """Will store any unrecognized kwargs in a dictionary of custom
        properties unless keep_customs is False."""
        custom = None
        if keep_customs:
            custom = kwargs
        self.custom = custom

    def get_custom(self, prop):
        """Returns the custom property, or None if it does not exist."""
        return self.custom.get(prop)

    def set_custom(self, prop, val):
        """Sets the custom property."""
        self.custom[prop] = val

    @classmethod
    def dummy(cls, **kwargs):
        """Creates a dummy object with generic, properly formed values."""
        return cls(**kwargs)

    @classmethod
    def standard_attrs(cls):
        """Returns a list of all the attributes this media object is
        expected to provide, and will set from kwargs on input."""
        return []

    @staticmethod
    def _parse_framerate(framerate, start_tc, end_tc):
        """Extracts a framerate from either a pair of Timecode objects or a
        framerate parameter and raises an Exception if any are
        incompatible."""
        framerates = [str(framerate)]
        framerates.append(str(getattr(start_tc, 'framerate', '')))
        framerates.append(str(getattr(end_tc, 'framerate', '')))
        framerates = list(filter(lambda x: x not in (None, '', 'None'), framerates))
        if conflicting_values(framerates):
            raise ValueError(f'Incompatible framerates {framerates} cannot ' +
                             'be used for timecodes on the same range.')
        try:
            return framerates[0]
        except IndexError:
            raise ValueError('Attempting to create timecode without valid ' +
                             'framerate.')

class Clip(Mob):
    """Parent object for any media object made from a single piece of
    media."""
    _provides_attrs = ['tape', 'source_file', 'reel', 'src_framerate',
                       'src_start_tc', 'src_end_tc', 'clip_name']

    def __init__(self, tape=None, source_file=None,
                 reel=None, src_framerate=None, src_start_tc=None,
                 src_end_tc=None, clip_name=None,
                 default_source_file=False, **kwargs):
        super(Clip, self).__init__(**kwargs)
        self.default_source_file = default_source_file
        self._set_reel(tape, source_file, reel)
        self.src_framerate = self._parse_framerate(src_framerate,
                                                   src_start_tc,
                                                   src_end_tc)
        self.src_start_tc = Timecode(self.src_framerate, src_start_tc)
        self.src_end_tc = Timecode(self.src_framerate, src_end_tc)
        self.clip_name = clip_name

    def real_seconds(self, tc):
        """Returns the time in seconds from start of clip to tc,
        considering fractional framerates."""
        return tc.real_seconds(self.src_start_tc)

    @classmethod
    def dummy(cls, **kwargs):
        """Creates a dummy object with generic, properly formed values."""
        defaults = dict(tape='SLUG',
                        src_framerate='24',
                        src_start_tc='00:01:00:00',
                        src_end_tc='00:01:10:00',
                        clip_name='Slug')
        defaults.update(kwargs)
        return super().dummy(**defaults)

    @property
    def src_duration(self):
        """Returns difference of src_end_tc and src_start_tc. Timecode durations
        are inclusive, eg 00:00:01:00 + 00:00:01:23 = 00:00:02:00, because
        00:00:00:23 == 24 frames."""
        return self.src_end_tc - self.src_start_tc

    def _set_reel(self, tape, source_file, reel):
        self.tape = None
        self.source_file = None
        if tape and source_file:
            if not self._equivalent_reel(tape, source_file):
                raise ValueError(f'Cannot create with incompatible tape: ' +
                                 '{tape} and source_file: {source_file}.')
            warn(f'Creating {self} with both tape {tape} and source_file ' +
                 '{source_file}. Will discard non-default source attribute.',
                 RuntimeWarning)
            if self.default_source_file:
                self.source_file = source_file
                return
            self.tape = tape
            return
        if tape is not None:
            self.tape = tape
            return
        if source_file is not None:
            self.source_file = source_file
            return
        if reel is not None:
            self.reel = reel
            return
        warn(f'Creating {self} without valid tape or source_file.', RuntimeWarning)

    @property
    def reel(self):
        """Returns either tape or source_file attribute. If both attributes are
        defined, returns tape unless default_source_file flag is set."""
        reels = (self.tape, self.source_file)
        if self.default_source_file:
            reels = reversed(reels)
        return next(filter(None, reels))

    @reel.setter
    def reel(self, val):
        """Sets tape unless default_source_file flag is set."""
        if self.default_source_file:
            self.source_file = val
            return
        self.tape = val

    @staticmethod
    def _equivalent_reel(tape, source_file):
        tape = tape.split('.', 1)[0].upper()
        source_file = source_file.split('.', 1)[0].upper()
        return tape == source_file

    @classmethod
    def standard_attrs(cls):
        """Returns a list of all the attributes this media object is
        expected to provide, and will set from kwargs on input."""
        return Clip._provides_attrs + super().standard_attrs()

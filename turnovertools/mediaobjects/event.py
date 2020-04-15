"""Event class, a general purpose object for events in edit sequences."""

from warnings import warn

from . import Timecode

def conflicting_values(values):
    """Returns True if iterable values contain more than one unique,
    non-None value, or no non-None values."""
    unique_values = dict.fromkeys(values, 1)
    unique_values = tuple(filter(None, unique_values))
    return len(unique_values) != 1

class Event:
    """Generic event in an edit sequence, references a source clip via tape
    or source_file attribute, which are elided into the reel property."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable-msg=too-many-locals
    # pylint: disable-msg=too-many-arguments
    #
    # we need as many attributes as the object spec requires. consider finding
    # logical subgroupings of attributes.
    def __init__(self, num=None, tape=None, source_file=None,
                 reel=None, tr_code=None, aux=None,
                 src_framerate=None, src_start_tc=None,
                 src_end_tc=None, rec_framerate=None,
                 rec_start_tc=None, rec_end_tc=None, clip_name=None,
                 default_source_file=False, track=None):
        self.default_source_file = default_source_file

        self.num = num
        self._set_reel(tape, source_file, reel)
        self.tr_code = tr_code
        self.aux = aux
        self.src_framerate = self._parse_framerate(src_framerate,
                                                   src_start_tc,
                                                   src_end_tc)
        self.src_start_tc = Timecode(self.src_framerate, src_start_tc)
        self.src_end_tc = Timecode(self.src_framerate, src_end_tc)
        self.rec_framerate = self._parse_framerate(rec_framerate,
                                                   rec_start_tc,
                                                   rec_end_tc)
        self.rec_start_tc = Timecode(self.rec_framerate, rec_start_tc)
        self.rec_end_tc = Timecode(self.rec_framerate, rec_end_tc)
        self.clip_name = clip_name
        self.track = track

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

    @property
    def src_duration(self):
        """Returns difference of src_end_tc and src_start_tc. Timecode durations
        are inclusive, eg 00:00:01:00 + 00:00:01:23 = 00:00:02:00, because
        00:00:00:23 == 24 frames."""
        return self.src_end_tc - self.src_start_tc

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
                        tape='SLUG',
                        tr_code='V',
                        aux='C',
                        src_framerate='24',
                        src_start_tc='00:01:00:00',
                        src_end_tc='00:01:10:00',
                        rec_framerate='24',
                        rec_start_tc='01:00:00:00',
                        rec_end_tc='01:00:10:00',
                        clip_name='Slug',
                        track=1)
        defaults.update(kwargs)
        return cls(**defaults)

    @staticmethod
    def _equivalent_reel(tape, source_file):
        tape = tape.split('.', 1)[0].upper()
        source_file = source_file.split('.', 1)[0].upper()
        return tape == source_file

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

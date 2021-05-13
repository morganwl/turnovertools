"""Child class for python-timecode package to resolve some issues
and provide additional needed functionality."""

from timecode import Timecode as TimecodeParent, TimecodeError

# Various representations of the same framerate
FRAMERATE_TABLE = {'23.976': '23.98',
                   '23.98': '23.98',
                   'ntsc-film': '23.98',
                   '24000/1001': '23.98',
                   '2997/125': '23.98',
                   '24': '24',
                   '24/1': '24',
                   'film': '24',
                   'pal': '25',
                   '25/1': '25',
                   '25': '25',
                   'ntsc': '29.97',
                   '29.97': '29.97',
                   '30000/1001': '29.97',
                   '30i': '29.97',
                   '30/1': '30',
                   '30': '30',
                   '60000/1001': '59.94',
                   '59.94': '59.94',
                   '60i': '59.94'}

class Timecode(TimecodeParent):
    """
    Child of python-timecode Timecode class, adding the following
    functionality:
      - ability to initialize a new Timecode object using an existing
        Timecode object as the start_timecode (with or without an
        explicitly stated framerate)
      - python3 floordiv support
      - create multiple Timecode objects from a single framerate and a
        collection of timecode strings
      - recognize 23.976 as the same as 23.98
      """

    def __init__(self, framerate_or_timecode, start_timecode=None,
                 **kwargs):
        """Creates a timecode object using a syntax of either
        Timecode(<Timecode object>), Timecode(framerate, <Timecode object>),
        Timecode(framerate, <str object>)"""
        # Timecode(<Timecode object>)
        try:
            framerate = framerate_or_timecode.framerate
        except AttributeError:
            framerate = framerate_or_timecode
        else:
            start_timecode = str(framerate_or_timecode)
        if start_timecode:
            # Timecode(framerate, <Timecode object>)
            try:
                other_framerate = start_timecode.framerate
            # Timecode(framerate, <str object>)
            except AttributeError:
                pass
            else:
                if round(float(framerate)) != round(float(other_framerate)):
                    raise ValueError(f'Need to explicitly convert ' +
                                     '{start_timecode} with framerate ' +
                                     '{other_framerate} to {self.__class__} '+
                                     'with framerate {framerate}.')
            start_timecode = str(start_timecode)
        framerate = self.normalize_framerate(framerate)
        # TO-DO: Check for drop-frame in a smarter way
        # TO-DO: Test for well-formed and poorly formed timecodes
        if start_timecode and len(start_timecode.replace(';', ':').split(':')) != 4:
            raise ValueError(f'Poorly formed timecode {start_timecode}.')
        f_framerate = float(framerate)
        if f_framerate == 23.98:
            f_framerate = 23.976
        self.f_framerate = f_framerate
        super(Timecode, self).__init__(framerate, start_timecode,
                                       **kwargs)

    # parent object returns new object with result, which we need to
    # cast to current objects type
    def __add__(self, other):
        if isinstance(other, int):
            frames = other
        elif hasattr(other, 'frames'):
            if self.framerate == other.framerate:
                frames = other.frames
            else:
                msg = ('Illegal mixed framerate timecode arithmetic: ' +
                       f'{self.framerate}, {other.framerate}')
                raise TimecodeError(msg)
        else:
            msg = (f'Type {other.__class__.__name__} not supported ' +
                   'for arithmetic.')
            raise TimecodeError(msg)
        frames += self.frames
        result = type(self)(self.framerate, frames=frames)
        result.f_framerate = self.f_framerate
        return result

    def __sub__(self, other):
        if isinstance(other, int):
            frames = other
        elif hasattr(other, 'frames'):
            if self.framerate == other.framerate:
                frames = other.frames
            else:
                msg = ('Illegal mixed framerate timecode arithmetic: ' +
                       f'{self.framerate}, {other.framerate}')
                raise TimecodeError(msg)
        else:
            msg = (f'Type {other.__class__.__name__} not supported ' +
                   'for arithmetic.')
            raise TimecodeError(msg)
        frames = self.frames - frames
        result = type(self)(self.framerate, frames=frames)
        result.f_framerate = self.f_framerate
        return result

    def __mul__(self, other):
        result = super(Timecode, self).__mul__(other)
        result = self.cast_to_current_type(result)
        result.f_framerate = self.f_framerate
        return result

    def offset(self, base):
        """Returns the timecode offset between self and base. Unlike
        substraction, this treats the offset timecode as inclusive,
        meaning that 00:00:00:01 - 00:00:00:00 is 00:00:00:01."""
        return self - base + 1

    def real_seconds(self, offset=None):
        """Returns the actual seconds, taking into account pulldown
        timecode, defaulting to an offset from 00:00:00:00."""
        if offset is not None:
            if hasattr(offset, 'framerate'):
                frames = self.offset(offset).frames
            else:
                frames = self.offset(Timecode(self.framerate, offset)).frames
        else:
            frames = self.frames
        print(frames - 1, self.f_framerate)
        return (frames - 1) / self.f_framerate

    # parent class implements __floordiv__ as __div__, because it is
    # from python2!
    def __floordiv__(self, other):
        """Returns a new Timecode instance with divided value, discarding any
        fractional remaining frames. (Maps to the __div__ method of
        the timecode.Timecode)"""
        result = self.__div__(other)
        result = self.cast_to_current_type(result)
        result.f_framerate = self.f_framerate
        return result

    @classmethod
    def cast_to_current_type(cls, obj):
        """Casts an object to the type of the calling object. (Could be
        mobs.Timecode or an inheriting class.)"""
        if not isinstance(obj, cls):
            obj = cls(obj)
        return obj

    @classmethod
    def from_set(cls, framerate, timecodes):
        """Given one framerate and an iterable collection of timecode
        literals, yields those timecodes as Timecode objects."""
        for timecode in timecodes:
            yield cls(framerate, timecode)

    @staticmethod
    def normalize_framerate(framerate):
        """Converts a variety of known framerate names to their
        corresponding Timecode framerate. Known framerates:
        '23.976', '23.98', '23.98', 'ntsc-film', '24', 'film', '24000/1001',
        'pal', '25', 'ntsc', '29.97', '30i', '3000/1001', '30', '59.94',
        '60i', '59.94'"""
        try:
            if float(framerate) == int(float(framerate)):
                framerate = int(float(framerate))
            else:
                framerate = round(float(framerate), 3)
        except ValueError:
            pass
        try:
            return FRAMERATE_TABLE[str(framerate)]
        except KeyError:
            raise FramerateError(f"Framerate '{framerate}' not recognized.")

class FramerateError(Exception):
    """Raised when an invalid framerate is used."""

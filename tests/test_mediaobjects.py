"""Tests mobs.Timecode and mobs.Event objects"""

import os
import unittest

from timecode import Timecode

from shared_test_setup import USER_HOME
from shared_test_setup import swap_key
from turnovertools import mediaobjects as mobs

# look for private test files in the home user directory that are not
# tracked by git
PRIVATE_TEST_FILES = os.path.join(USER_HOME, 'private_test_files',
                                  'turnovertools', 'mediaobjects')
PRIVATE_TEST_MEDIA = os.path.join(PRIVATE_TEST_FILES, 'test_media')
PRIVATE_TEST_AVID_VOLUME = os.path.join(PRIVATE_TEST_MEDIA,
                                        'test_media_volume')
PRIVATE_CONTROL_SAMPLES = os.path.join(PRIVATE_TEST_FILES,
                                       'control_samples', 'mediaobjects')

def get_sample_event_data():
    """Returns a dictionary of sample event data."""
    sample_data = dict(
        num='5',
        tape='A001C001_200410_AZAZ',
        tr_code='V',
        aux='C',
        src_framerate='24',
        src_start_tc='05:00:03:00',
        src_end_tc='05:00:10:12',
        rec_framerate='24',
        rec_start_tc='01:00:00:00',
        rec_end_tc='01:00:10:12',
        clip_name='event_test_001',
        track=1)
    return sample_data

class TestMobsUtility(unittest.TestCase):
    """Tests some utility functions in the mediaobjects subpackage."""
    def setUp(self):
        pass

    def test_conflicting_values(self):
        """Sends some different sets of values and makes sure that sets
        containing disparate values return True and sets containing
        values that evaluate to the same string return False."""
        self.assertTrue(mobs.conflicting_values((1, 1, 2)))
        self.assertFalse(mobs.conflicting_values(('a', None, 'a', 'a')))
        self.assertTrue(mobs.conflicting_values((1, '1', 1)))

class TestMobsTimecode(unittest.TestCase):
    """The mobs.Timecode class should be a pass-through to
    timecode.Timecode, with some better generation functionality."""

    def setUp(self):
        pass

    def test_timecode_creation_with_string(self):
        """Checks to see that mobs.Timecode and Timecodes created with
        the same strings return the same values."""
        timecode = Timecode(24, '01:00:00:00')
        mobs_timecode = mobs.Timecode(24, '01:00:00:00')
        self.assertEqual(mobs_timecode, timecode)
        self.assertEqual(mobs.Timecode('23.98', '03:00:00:00'),
                         Timecode('23.98', '03:00:00:00'))

    def test_2398_equals_23976(self):
        """Checks that framerates of 23.976 and 23.98 (two names for
        24fps pulldown timecode) are interpeted the same way."""
        self.assertEqual(mobs.Timecode('23.98', '05:00:00:00'),
                         mobs.Timecode('23.976', '05:00:00:00'))
        self.assertEqual(mobs.Timecode('23.98', '05:00:00:00').frames,
                         mobs.Timecode('23.976', '05:00:00:00').frames)
        self.assertEqual(mobs.Timecode(23.98, '05:00:00:00'),
                         mobs.Timecode(23.976, '05:00:00:00'))
        self.assertEqual(mobs.Timecode(23.98, '05:00:00:00').frames,
                         mobs.Timecode(23.976, '05:00:00:00').frames)

    def test_2398_frames_equals_24_frames(self):
        """Checks that timecodes with true 24 and pulldown 24 framerates
        have the same number of frames for any given timecode."""
        tc24 = mobs.Timecode(24, '01:00:00:00')
        tc2398 = mobs.Timecode(23.98, '01:00:00:00')
        for addend in range(0, 24 * 60 * 60 * 22, 993):
            self.assertEqual((tc24 + addend).frames,
                             (tc2398 + addend).frames)

    def test_pulldown_framerates_arithmetic(self):
        """Checks that operations on mobs.Timecode objects with
        framerate 23.98 have the same result as operations on objects
        with framerate 24."""
        tc24 = mobs.Timecode(24, '01:00:00:00')
        tc2398 = mobs.Timecode(23.98, '01:00:00:00')
        for addend in range(0, 24 * 60 * 60 * 22, 163):
            self.assertEqual(str(tc24 + addend),
                             str(tc2398 + addend))

    def test_timecode_creation_with_timecode(self):
        """Checks to see that a mobs.Timecode created with a Timecode
        returns the same value as the original Timecode."""
        timecode = Timecode(24, '01:10:10:23')
        mobs_timecode = mobs.Timecode(24, timecode)
        self.assertEqual(mobs_timecode, timecode)

    def test_timecode_creation_with_timecode_and_no_framerate(self):
        """Cast a Timecode object to a mobs.Timecode object directly, without
        specifying a framerate (since the Timecode object already has
        one)."""
        timecode = Timecode(24, '01:10:10:23')
        mobs_timecode = mobs.Timecode(timecode)
        self.assertEqual(mobs_timecode, timecode)

    def test_timecode_from_set(self):
        """Return a set of timecodes with the same framerate."""
        framerate = 24
        str_timecodes = ('01:10:10:23', '01:10:12:23', '01:10:15:23')
        timecodes = (Timecode(framerate, str_timecode) for str_timecode in str_timecodes)
        mobs_timecodes = mobs.Timecode.from_set(framerate, str_timecodes)
        for mobs_timecode, timecode in zip(mobs_timecodes, timecodes):
            self.assertEqual(mobs_timecode, timecode)

    def test_arithmetic_returns_mobs_timecode(self):
        """Arithmetic operations should return object of the same class, not
        the parent class."""
        timecode = mobs.Timecode(24, '01:00:00:00')
        other_timecode = mobs.Timecode(24, '00:00:30:00')
        other_int = 721
        self.assertIsInstance(timecode + other_timecode, type(timecode))
        self.assertIsInstance(timecode + other_int, type(timecode))
        self.assertIsInstance(timecode - other_timecode, type(timecode))
        self.assertIsInstance(timecode - other_int, type(timecode))
        self.assertIsInstance(timecode * other_timecode, type(timecode))
        self.assertIsInstance(timecode * other_int, type(timecode))
        self.assertIsInstance(timecode // other_timecode, type(timecode))
        self.assertIsInstance(timecode // other_int, type(timecode))

    def test_timecode_division(self):
        """Need to think through what a **desirable** behavior for Timecode
        division would be, based on the ways in which Timecode stores frame
        numbers."""
        timecode = mobs.Timecode(24, '01:00:00:00')
        expected_result = mobs.Timecode(24, '00:29:59:23')
        self.assertEqual(timecode // 2, expected_result)

    def test_timecode_exception_on_mismatched_framerates(self):
        """Creates a mobs.Timecode with an explicit framerate, but
        passes a Timecode object with a different framerate."""
        timecode = Timecode(30, '01:10:10:23')
        with self.assertRaises(ValueError):
            mobs.Timecode(24, timecode)

class TestEventObject(unittest.TestCase):
    """The Event object represents an event in a sequence."""

    def setUp(self):
        self.sample_event_data = dict(
            num='5',
            tape='A001C001_200410_AZAZ',
            tr_code='V',
            aux='C',
            src_framerate='24',
            src_start_tc='05:00:03:00',
            src_end_tc='05:00:10:12',
            rec_framerate='24',
            rec_start_tc='01:00:00:00',
            rec_end_tc='01:00:10:12',
            clip_name='event_test_001',
            track=1)

    def test_event_creation_from_kwargs(self):
        """We should be able to create an event using keyword arguments for
        all expected attributes."""
        event = mobs.Event(**self.sample_event_data)
        for attribute, val in self.sample_event_data.items():
            self.assertEqual(str(getattr(event, attribute)), str(val))

    def test_dummy_creation(self):
        """Checks that a dummy event is able to be created, modified,
        and that the values can be overridden by kwargs."""
        event = mobs.Event.dummy()
        for attribute, val in self.sample_event_data.items():
            setattr(event, attribute, val)
            self.assertEqual(str(getattr(event, attribute)), str(val))
        event = mobs.Event.dummy(**get_sample_event_data())
        for attribute, val in get_sample_event_data().items():
            self.assertEqual(str(getattr(event, attribute)), str(val))

    def test_creation_with_timecode_obj(self):
        """Should be able to create an event using string timecode or Timecode
        attribute, so long as the proper framerates are given."""
        sample_data = self.sample_event_data.copy()
        sample_data['src_start_tc'] = Timecode(sample_data['src_framerate'],
                                               sample_data['src_start_tc'])
        sample_data['src_end_tc'] = Timecode(sample_data['src_framerate'],
                                             sample_data['src_end_tc'])
        event = mobs.Event(**sample_data)
        for attribute, val in self.sample_event_data.items():
            self.assertEqual(str(getattr(event, attribute)), str(val))

    def test_creation_with_source_file(self):
        """An event should have a mutually exclusive source_file or tape
        attribute."""
        sample_data = self.sample_event_data.copy()
        sample_data['source_file'] = sample_data['tape']
        del sample_data['tape']
        event = mobs.Event(**sample_data)
        for attribute, val in self.sample_event_data.items():
            if attribute == 'tape':
                self.assertIsNone(event.tape)
                self.assertEqual(event.source_file, val)
                continue
            self.assertEqual(str(getattr(event, attribute)), str(val))

    def test_warns_on_tape_and_source_file(self):
        """Attempting to create an event with equivalent tape and source_file
        values should warn, but create an event using the default
        source attribute. """
        sample_data = self.sample_event_data.copy()
        # Exactly equal
        sample_data['source_file'] = sample_data['tape']
        with self.assertWarns(RuntimeWarning):
            event = mobs.Event(**sample_data)
        for attribute, val in self.sample_event_data.items():
            self.assertEqual(str(getattr(event, attribute)), str(val))
        # With different extension
        sample_data['source_file'] = sample_data['source_file'] + '.mov'
        with self.assertWarns(RuntimeWarning):
            event = mobs.Event(**sample_data)
        for attribute, val in self.sample_event_data.items():
            self.assertEqual(str(getattr(event, attribute)), str(val))
        # With different case
        sample_data['source_file'] = sample_data['source_file'].lower()
        with self.assertWarns(RuntimeWarning):
            event = mobs.Event(**sample_data)
        for attribute, val in self.sample_event_data.items():
            self.assertEqual(str(getattr(event, attribute)), str(val))


    def test_exception_on_disparate_tape_and_source_file(self):
        """Attempting create an event where tape and source_file are both
        given and unequivalent should raise an exception."""
        self.sample_event_data['source_file'] = 'different_source'
        with self.assertRaises(ValueError):
            mobs.Event(**self.sample_event_data)

    def test_reel(self):
        """An event should have a reel property that returns either the
        source_file or the tape, and can be used to set the default field."""
        # When the source attribute is tape
        event = mobs.Event(**self.sample_event_data)
        self.assertEqual(event.reel, self.sample_event_data['tape'])
        # When the source attribute is source_file
        sample_data = self.sample_event_data.copy()
        swap_key(sample_data, 'tape', 'source_file')
        event = mobs.Event(**sample_data)
        self.assertEqual(event.reel, self.sample_event_data['tape'])
        swap_key(sample_data, 'source_file', 'reel')
        event = mobs.Event(**sample_data)
        self.assertEqual(event.reel, self.sample_event_data['tape'])

    def test_src_duration(self):
        """src_duration should return the timecode duration between the
        src_start_timecode and src_end_timecode."""
        start = mobs.Timecode(24, '01:00:00:00')
        end = mobs.Timecode(24, '01:00:00:00')
        for offset in range(1, 250):
            event = mobs.Event.dummy(src_start_tc=start, src_end_tc=end+offset)
            self.assertEqual(event.src_duration.frames, offset)

    @unittest.skipIf(os.environ.get('SKIP_PLANNED_TESTS', False), 'Skipping planned test.')
    def test_set_reel_sets_source_file(self):
        """Reel should default to setting tape, but should be able to be
        changed to source_file."""

    @unittest.skipIf(os.environ.get('SKIP_PLANNED_TESTS', False), 'Skipping planned test.')
    def test_event_custom_attributes_from_kwargs(self):
        """Unknown attributes should be placed under the event.custom attribute."""
        self.fail('Not implemented.')

    @unittest.skipIf(os.environ.get('SKIP_PLANNED_TESTS', False), 'Skipping planned test.')
    def test_event_creation_from_event(self):
        """An event or event-like object should be copyable at creation."""
        self.fail('Not implemented.')

    @unittest.skipIf(os.environ.get('SKIP_PLANNED_TESTS', False), 'Skipping planned test.')
    def test_event_custom_attributes_from_event(self):
        """Unexpected attributes from an event should be placed under the
        event.custom attribute."""
        self.fail('Not implemented.')

    @unittest.skipIf(os.environ.get('SKIP_PLANNED_TESTS', False), 'Skipping planned test.')
    def test_event_expected_attributes(self):
        """An event should have dependable attributes."""
        self.fail('Not implemented.')

    @unittest.skipIf(os.environ.get('SKIP_PLANNED_TESTS', False), 'Skipping planned test.')
    def test_event_locators(self):
        """An event should be able to have an arbitrary number of markers,
        with timecode, color, user and comment."""
        self.fail('Not implemented.')

    @unittest.skipIf(os.environ.get('SKIP_PLANNED_TESTS', False), 'Skipping planned test.')
    def test_event_creation_from_clip(self):
        """An event should be able to be created using another, non-event,
        media object."""
        self.fail('Not implemented.')

    @unittest.skipIf(os.environ.get('SKIP_PLANNED_TESTS', False), 'Skipping planned test.')
    def test_event_to_dict(self):
        """An event should be able to output itself as a dictionary."""
        self.fail('Not implemented.')

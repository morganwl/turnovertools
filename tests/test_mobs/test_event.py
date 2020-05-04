"""Tests mobs.Timecode and mobs.Event objects"""

import os
import unittest

from timecode import Timecode

from tests.shared_test_setup import USER_HOME
from tests.shared_test_setup import swap_key
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

    @unittest.skip('Skipping planned test.')
    def test_set_reel_sets_source_file(self):
        """Reel should default to setting tape, but should be able to be
        changed to source_file."""

    @unittest.skip('Skipping planned test.')
    def test_event_custom_attributes_from_kwargs(self):
        """Unknown attributes should be placed under the event.custom attribute."""
        self.fail('Not implemented.')

    @unittest.skip('Skipping planned test.')
    def test_event_creation_from_event(self):
        """An event or event-like object should be copyable at creation."""
        self.fail('Not implemented.')

    @unittest.skip('Skipping planned test.')
    def test_event_custom_attributes_from_event(self):
        """Unexpected attributes from an event should be placed under the
        event.custom attribute."""
        self.fail('Not implemented.')

    @unittest.skip('Skipping planned test.')
    def test_event_expected_attributes(self):
        """An event should have dependable attributes."""
        self.fail('Not implemented.')

    @unittest.skip('Skipping planned test.')
    def test_event_locators(self):
        """An event should be able to have an arbitrary number of markers,
        with timecode, color, user and comment."""
        self.fail('Not implemented.')

    @unittest.skip('Skipping planned test.')
    def test_event_creation_from_clip(self):
        """An event should be able to be created using another, non-event,
        media object."""
        self.fail('Not implemented.')

    @unittest.skip('Skipping planned test.')
    def test_event_to_dict(self):
        """An event should be able to output itself as a dictionary."""
        self.fail('Not implemented.')

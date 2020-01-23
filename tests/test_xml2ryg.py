import logging
import os
import sys
import unittest

TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from scripts import xml2ryg
from turnovertools import mediaobject

TEST_FILES = os.path.join(TEST_DIR, 'test_files')
TEST_XML_COMPLEX = os.path.join(TEST_FILES, 'R2-v29_Flattened.xml')

class TestXml2rygInternals(unittest.TestCase):
    def setUp(self):
        self.input = TEST_XML_COMPLEX
        self.events = xml2ryg.events_from_xml(TEST_XML_COMPLEX)

    def test_input_xml(self):
        events = xml2ryg.events_from_xml(TEST_XML_COMPLEX)
        for i, e in enumerate(events):
            with self.subTest(i=i):
                self.assertIsInstance(e, mediaobject.Event)

    def test_sort_events_by_timecode(self):
        sorted_events = xml2ryg.sort_by_tc(self.events)
        previous_timecode = ''
        previous_track = ''
        for i, e in enumerate(sorted_events):
            this_timecode = e.rec_start_tc
            this_track = e.parent.track_name
            with self.subTest(i=i):
                self.assertGreaterEqual(this_timecode, previous_timecode)
                if this_timecode == previous_timecode:
                    self.assertGreater(this_track, previous_track)
            previous_timecode = this_timecode
            previous_track = this_track

    def test_remove_filler(self):
        expected_filler_indices = [1, 90, 257, 273, 276, 279, 287, 293, 
                                   297, 299, 302, 307, 309, 311, 313, 
                                   315, 320, 322, 323, 324]
        for i, e in enumerate(self.events):
            remove_filler = xml2ryg.remove_filler(e)
            if remove_filler is None and i not in expected_filler_indices:
                with self.subTest(i=i):
                    self.fail('Unexpected event marked as filler.')
            elif remove_filler is not None and i in expected_filler_indices:
                with self.subTest(i=i):
                    self.fail('Expected filler event not marked as filler.')

    @unittest.skip('Feature postponed')
    def test_compare_existing(self):
        self.fail('Unwritten test.')

    def test_guess_metadata(self):
        for e in self.events:
            xml2ryg.guess_metadata(e)

    @unittest.skip('Feature postponed')
    def test_include_update_sheet(self):
        self.fail('Unwritten test.')

    def test_csv_output(self):
        self.fail('Unwritten test.')

    def test_frame_output(self):
        self.fail('Unwritten test.')

    def test_video_output(self):
        self.fail('Unwritten test.')

class TestXml2rygCommandLine(unittest.TestCase):
    def setUp(self):
        pass

    def test_commandline(self):
        self.fail('Unwritten test.')

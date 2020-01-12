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

    def test_input_xml(self):
        events = xml2ryg.events_from_xml(TEST_XML_COMPLEX)
        for i, e in enumerate(events):
            with self.subTest(i=i):
                self.assertIsInstance(e, mediaobject.Event)

    def test_sort_events_by_timecode(self):
        self.fail('Unwritten test.')

    def test_remove_filler(self):
        self.fail('Unwritten test.')

    def test_compare_existing(self):
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

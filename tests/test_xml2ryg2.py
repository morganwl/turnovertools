import csv
import logging
import os
import sys
import tempfile
import unittest

USER_HOME = os.path.expanduser("~")
TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from scripts import xml2ryg2
from turnovertools import mediaobject

TEST_FILES = os.path.join(TEST_DIR, 'test_files')

# look for private test files in the home user directory that are not tracked by git
PRIVATE_TEST_FILES = os.path.join(USER_HOME, 'private_test_files', 'turnover_tools')
TEST_EDL = os.path.join(PRIVATE_TEST_FILES, 'LG_R1_20200303_v34.Copy.01.edl')

class TestXml2ryg2Internals(unittest.TestCase):
    def setUp(self):
        self.input = TEST_EDL
        self.events = xml2ryg2.events_from_edl(TEST_EDL)

    def test_input_edl(self):
        events = xml2ryg2.events_from_edl(TEST_EDL)
        for i, e in enumerate(events):
            with self.subTest(i=i):
                self.assertIsInstance(e, mediaobject.Event)

    def test_process_events(self):
        xml2ryg2.process_events(self.events)

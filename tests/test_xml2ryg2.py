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
from turnovertools import mediaobject, linkfinder

TEST_FILES = os.path.join(TEST_DIR, 'test_files')

# look for private test files in the home user directory that are not tracked by git
PRIVATE_TEST_FILES = os.path.join(USER_HOME, 'private_test_files', 'turnovertools')
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

    @unittest.skip('need shorter, faster edl')
    def test_process_events(self):
        xml2ryg2.process_events(self.events)

    def test_process_events_getty_still(self):
        pass

    def test_process_events_ale(self):
        pass

    def test_process_events_footage_tracker(self):
        pass

    def test_process_events_qing_art(self):
        pass

    def test_process_events_shutterstock_still(self):
        pass

    @unittest.skip('need shorter, faster edl')
    def test_output_csv(self):
        temp_output = tempfile.NamedTemporaryFile(mode='w+', newline='')
        xml2ryg2.process_events(self.events)
        xml2ryg2.output_csv(self.events, xml2ryg2.Config.OUTPUT_COLUMNS, temp_output)
        temp_output.seek(0)
        for line in temp_output:
            print(line)        

    #@unittest.skip('')
    def test_all_matchers(self):
        xml2ryg2.process_events(self.events)
        for e in self.events:
            with self.subTest(tape=e.reel):
                self.assertIsNotNone(e.link)

class TestLinkfinderMatchers(unittest.TestCase):
    def setUp(self):
        self.matchers = xml2ryg2.Config.MATCHERS

    def test_GETTYIMAGES_520720101_01_LOW_RES(self):
        self.assertIsNotNone(linkfinder.process('GETTYIMAGES-520720101-01-LOW_RES', self.matchers))

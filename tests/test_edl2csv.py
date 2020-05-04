import os
import sys
import tempfile
import unittest

from timecode import Timecode

USER_HOME = os.path.expanduser("~")
TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from scripts import edl2csv
from turnovertools import edl
import turnovertools.mediaobjects as mobs
from turnovertools.mediaobjects import Event#, Locator

TEST_FILES = os.path.join(TEST_DIR, 'test_files')

# look for private test files in the home user directory that are not
# tracked by git
PRIVATE_TEST_FILES = os.path.join(USER_HOME, 'private_test_files',
                                  'turnovertools', 'vfx')
MIXED_RATE_EDL = os.path.join(PRIVATE_TEST_FILES, 'mixed_framerate.edl')
MIXED_RATE_EDL_EXPECTED_SRC_TC = [('17:17:10:13', '17:17:13:21'),
                                  ('00:51:00:15', '00:51:02:25'),
                                  ('00:50:38:07', '00:50:40:20'),
                                  ('00:49:30:02', '00:49:33:13'),
                                  ('00:05:12:11', '00:05:15:13'),
                                  ('17:19:16:10', '17:19:21:16'),]

class TestMixedRateEdl(unittest.TestCase):
    def setUp(self):
        self.edl = edl.import_edl(MIXED_RATE_EDL)

    def test_source_timecode(self):
        for e, (src_start, src_end) in zip(self.edl,
                                           MIXED_RATE_EDL_EXPECTED_SRC_TC):
            self.assertEqual(str(e.src_start_tc), src_start)
            self.assertEqual(str(e.src_end_tc), src_end)

    def test_read_vfx_locators(self):
        """Inputs an event and, if that event has a properly formatted
        locator, expects a vfxevent back."""
        event = Event.dummy(rec_start_tc='01:00:00:00')
        event = edl2csv.read_vfx_locators(event)
        #Event.dummy(rec_start_tc='01:01:00:00',
        #            locators=[Locator('01:01:00:12',
        #                              'Blue',
        #                              'new')]),
        #Event.dummy(rec_start_tc='01:02:00:00',
        #            locators=[('01:02:01:00',
        #                       'Blue',
        #                       'old'),
        #                      ('01:02:01:02',
        #                       'Yellow',
        #                       'vfx=test_001_020=el01=do vfx')])

""""""

import csv
import os
import sys
import tempfile
import unittest

USER_HOME = os.path.expanduser("~")
TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from tests.test_mobs import get_sample_vfxevent_data
from turnovertools import vfxlist

# look for private test files in the home user directory that are not
# tracked by git
PRIVATE_TEST_FILES = os.path.join(USER_HOME, 'private_test_files',
                                  'turnovertools', 'mediaobjects')
PRIVATE_TEST_MEDIA = os.path.join(PRIVATE_TEST_FILES, 'test_media')
PRIVATE_TEST_AVID_VOLUME = os.path.join(PRIVATE_TEST_MEDIA,
                                        'test_media_volume')

PRIVATE_CONTROL_SAMPLES = os.path.join(PRIVATE_TEST_FILES,
                                       'control_samples', 'mediaobjects')

class TestVFXList(unittest.TestCase):
    def setUp(self):
        pass

    def test_read_vfx_csv_vfxevents(self):
        """Receives an iterable string (eg file object or list object)
        containing a csv formatted event list and returns a list of only VFX
        items as mobs."""
        sample_data = [get_sample_vfxevent_data()]
        with tempfile.TemporaryFile('w+t', newline='') as filehandle:
            writer = csv.DictWriter(filehandle, fieldnames=sample_data[0])
            writer.writeheader()
            for vfx in sample_data:
                writer.writerow(vfx)
            filehandle.seek(0)
            vfxitems = vfxlist.read_vfx_csv(filehandle)
        for vfxevent, vfx_sample in zip(vfxitems, sample_data):
            for attribute, val in vfx_sample.items():
                self.assertEqual(str(getattr(vfxevent, attribute)), str(val))

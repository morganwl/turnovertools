"""Tests the Clip base object."""

import datetime
import unittest

import turnovertools.mediaobjects as mobs

class TestClip(unittest.TestCase):
    """Tests the functionality of the Clip class."""

    def test_create_from_dict(self):
        clip = mobs.Clip(**{'clip_name': 'source_with_tape_name',
                            'link': 'https://www.youtube.com/watch?v=x4xCSVl833I',
                            'src_framerate': '23.98',
                            'tape': 'A001C001',
                            'src_start_tc': '01:00:00:00',
                            'src_end_tc': '01:00:10:00',})
        print(clip.src_start_tc)
        self.assertIsNotNone(clip)

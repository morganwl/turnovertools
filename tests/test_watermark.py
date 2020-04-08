import csv
from itertools import zip_longest
import logging
import os
import sys
import tempfile
import unittest

from timecode import Timecode

USER_HOME = os.path.expanduser("~")
TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from turnovertools import fftools, watermark
from scripts import vfxreference

TEST_FILES = os.path.join(TEST_DIR, 'test_files')

# look for private test files in the home user directory that are not
# tracked by git
PRIVATE_TEST_FILES = os.path.join(USER_HOME, 'private_test_files',
                                  'turnovertools', 'vfx')
PRIVATE_CONTROL_SAMPLES = os.path.join(PRIVATE_TEST_FILES,
                                       'control_samples')
REFERENCE_QT_CONTROL_DIR = os.path.join(PRIVATE_CONTROL_SAMPLES,
                                        'LG_VFX_R2_REFERENCE')
TEST_VFX_LIST = os.path.join(PRIVATE_TEST_FILES,
                             'LG_R2_20200325_VFX_Snippet.csv')

def compare_vid(vid, other, pix_fmt='gray', scale=(960, 540)):
    vid_stream = fftools.interval_stream_frames(
        vid, interval=1, scale=scale, pix_fmt=pix_fmt)
    other_stream = fftools.interval_stream_frames(
        other, interval=1, scale=scale, pix_fmt=pix_fmt)
    for vid_frame, other_frame in zip_longest(vid_stream,
                                              other_stream):
        yield fftools.mse(vid_frame, other_frame)

class TestWatermark(unittest.TestCase):
    def setUp(self):
        self.mediadir = PRIVATE_TEST_FILES
        self.clean_video_path = os.path.join(self.mediadir,
                                             'LG_R2_20200325_v55.mxf')
        self.clean_video = fftools.probe_clip(self.clean_video_path)
        self.metadata = { 'vfx_id': 'test',
                          'vfx_brief': 'test brief',
                          'rec_start_tc': Timecode(24, '02:00:06:00'),
                          'rec_end_tc': Timecode(24, '02:00:8:01'),
                          'frame_count_start': 1001,
                          'sequence_name': 'test'}

    def test_range_to_real_dur(self):
        start = Timecode(24, '01:00:08:00')
        end = Timecode(24, '01:00:10:00')
        for i in range(100):
            dur = watermark.range_to_real_dur(start + i*12, end + i*12, 23.976)
            self.assertEqual(int(dur*100), 200)
    
    @unittest.skip
    def test_write_video_with_watermark(self):
        wm = watermark.RecBurn(**self.metadata)
        watermark.write_video_with_watermark(self.clean_video,
                                             wm,
                                             start=self.metadata['rec_start_tc'],
                                             end=self.metadata['rec_end_tc'])
        

class TestVFXReference(unittest.TestCase):
    def setUp(self):
        self.vfxlist = TEST_VFX_LIST
        self.mediadir = PRIVATE_TEST_FILES
        self.control_path = REFERENCE_QT_CONTROL_DIR
        self.control_videos = sorted(file for file in 
                                     (os.listdir(
                    REFERENCE_QT_CONTROL_DIR)) if not file.startswith('.'))

    @unittest.skip("Don't want to run the watermark output any more times than we have to until we get tighter test samples.")
    def test_vfx_reference_count(self):
        with tempfile.TemporaryDirectory() as outputdir:
            vfxreference.main(self.vfxlist, self.mediadir, outputdir)
            results = sorted(os.listdir(outputdir))
            for result, control in zip(results, self.control_videos):
                self.assertEqual(result, control)

    def test_vfx_reference_image_comparison(self):
        with tempfile.TemporaryDirectory() as outputdir:
            vfxreference.main(self.vfxlist, self.mediadir, outputdir)
            results = sorted(os.listdir(outputdir))
            r0 = os.path.join(outputdir, results[0])
            c0 = os.path.join(self.control_path, self.control_videos[0])
            for i, err in enumerate(compare_vid(r0, c0)):
                #with self.subTest(frame_no=i):
                self.assertLess(err, 10)

#!/usr/bin/env python3

# I need to be able to export a pull list from FileMaker and turn that
# into:

#   - an ALE for all pulls, split by src_framerate
#   - an EDL for all pulls, split by src_framerate
#   - a reference quicktime for each set of pulls, split by src_framerate
#     - with appropriate burn-ins

from hashlib import md5 as checksum
import inspect
import os
import subprocess
import sys
import tempfile
import traceback
import unittest

from timecode import Timecode

USER_HOME = os.path.expanduser("~")
TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from scripts import vfxpull
#from turnovertools import edl

EXECUTABLE_DIR = os.path.join(MAIN_DIR, 'scripts')
VFXPULL_EXECUTABLE = os.path.join(EXECUTABLE_DIR, 'vfxpull.py')
TEST_FILES = os.path.join(TEST_DIR, 'test_files')

# look for private test files in the home user directory that are not
# tracked by git
PRIVATE_TEST_FILES = os.path.join(USER_HOME, 'private_test_files',
                                  'turnovertools', 'vfx')
PRIVATE_TEST_MEDIA = os.path.join(PRIVATE_TEST_FILES, 'test_media')
PRIVATE_TEST_AVID_VOLUME = os.path.join(PRIVATE_TEST_MEDIA,
                                        'test_media_volume')

PRIVATE_CONTROL_SAMPLES = os.path.join(PRIVATE_TEST_FILES,
                                       'control_samples', 'vfxpull')

def backup_environ(environ_vars):
    """Returns a dictionary containing the current state of a list of
    environment variables."""
    backup_environ = dict()
    for var in environ_vars:
        # if the environment variable doesn't exist, backup will be
        # set to None. These variables will be deleted from the
        # environment when restore_environ is called.
        backup_environ[var] = os.environ.get(var)
    return backup_environ

def restore_environ(backup_environ):
    """Updates the os.environ with a dictionary of values, deleting
    elements from the environment which are None in the supplied
    dictionary."""
    for var, val in backup_environ.items():
        if val is None:
            del os.environ[var]
        else:
            os.environ[var] = val

def on_fail(call_on_fail):
    def deco(test):
        def decorated(obj, *args, **kwargs):
            try:
                test(obj, *args, **kwargs)
            except Exception as exception:
                raise type(exception)(str(exception) + '\n' +
                                      call_on_fail(obj, exception))
        return decorated
    return deco

def inspect_subprocess(obj, exception):
    msg = ''
    if hasattr(obj, 'process'):
        process = obj.process
        msg += 'Failure of subprocess \n' + ' '.join(process.args)
        msg += '\n   Standard output:\n'
        msg += process.stdout
        msg += '\n   Standard error:\n'
        msg += process.stderr
    return msg
    
class TestVFXPullEndToEndSimple(unittest.TestCase):
    """Running vfxpull.py on a simple turnovertools formatted VFX list
    should output a single ALE with subclips for each shot, with
    specified handles, a single EDL with events for each shot, with
    specified handles, and a QuickTime reference video, with burnins,
    matching the pull EDL."""

    test_csv = os.path.join(PRIVATE_TEST_FILES,
                            'simple_vfx_pull.csv')
    control_ale = os.path.join(PRIVATE_CONTROL_SAMPLES,
                               'simple_vfx_pull_24.ale')
    control_edl = os.path.join(PRIVATE_CONTROL_SAMPLES,
                               'simple_vfx_pull_24.edl')
    control_mov = os.path.join(PRIVATE_CONTROL_SAMPLES,
                               'simple_vfx_pull_24.mov')
    args = ()

    @classmethod
    def setUpClass(cls):
        cls.outputdir_obj = tempfile.TemporaryDirectory()
        cls.outputdir = cls.outputdir_obj.name

        cls.expected_ale = os.path.join(cls.outputdir,
                                        'simple_vfx_pull_24.ale')
        cls.expected_edl = os.path.join(cls.outputdir,
                                        'simple_vfx_pull_24.edl')
        cls.expected_mov = os.path.join(cls.outputdir,
                                        'simple_vfx_pull_24.mov')

        cls.backupdir = os.getcwd()
        os.chdir(cls.outputdir)

        tmp_media_db = os.path.join(cls.outputdir, 'tmp_media_db.db')

        # create a temporary environment as a copy of the current
        # environ, then tweak it
        tmp_environ = os.environ.copy()
        tmp_environ.update({
                'VFX_MEDIA_VOLUMES': PRIVATE_TEST_AVID_VOLUME,
                'VFX_MEDIA_DATABASE': tmp_media_db
            })

        cls.process = subprocess.run(('python',
                                      VFXPULL_EXECUTABLE,
                                      cls.test_csv,
                                      cls.outputdir,
                                      *cls.args),
                                     capture_output=True,
                                     env=tmp_environ,
                                     text=True)

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.backupdir)
        cls.outputdir_obj.cleanup()
        del cls.outputdir_obj

    def test_process_completion(self):
        output = f'{self.process.stdout}\n{self.process.stderr}'
        self.assertEqual(self.process.returncode, 0, msg=output)

    def test_expected_ale(self):
        """Compares the ALE output of a simple VFX pull to a sample file."""
        with open(os.path.join(self.outputdir,
                               'simple_vfx_pull_24.ale')) as fh:
            output_ale = fh.read()
        with open(self.control_ale) as fh:
            expected_ale = fh.read()
        self.assertEqual(output_ale, expected_ale)

    def test_expected_edl(self):
        """Compares the EDL output of a simple VFX pull to a sample file."""
        with open(self.expected_edl) as fh:
            output_edl = fh.read()
        with open(self.control_edl) as fh:
            expected_edl = fh.read()
        self.maxDiff = 2000
        self.assertEqual(output_edl, expected_edl)

    @unittest.skip("Haven't gotten to this feature yet.""")
    def test_expected_quicktimes(self):
        """Compares the QuickTime output of a simple VFX pull to a sample
        quicktime."""
        # we should really be doing image comparison, but we'll do
        # exact file comparison for now
        output_mov_checksum = checksum()
        expected_mov_checksum = checksum()
        chunk_size = 1024*32
        with open(os.path.join(self.outputdir,
                               'simple_vfx_pull.mov'), 'rb') as fh:
            chunk = fh.read(chunk_size)
            while chunk:
                output_mov_checksum.update(chunk)
                chunk = fh.read(chunk_size)
            output_mov_checksum.update(chunk)
        with open(self.control_mov, 'rb') as fh:
            chunk = fh.read(chunk_size)
            while chunk:
                expected_mov_checksum.update(chunk)
                chunk = fh.read(chunk_size)
            expected_mov_checksum.update(chunk)
        self.assertEqual(output_mov_checksum, expected_mov_checksum)

    def test_expected_output_files(self):
        """Checks to see that only the expected files are output."""
        output_files = os.listdir(self.outputdir)
        expected_files = ['simple_vfx_pull_24.ale',
                          'simple_vfx_pull_24.edl',]
#                          'simple_vfx_pull_24.mov']
        self.assertEqual(output_files, expected_files)

    def test_std_err(self):
        """Process should run without any errors."""
        self.assertIsNotNone(self.process.stderr)

class TestVFXPullEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # use me for any lengthy steps that we don't want to run too
        # many times
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_expected_mixed_rate_ale(self):
        """Compares the ALE output of a mixed-rate VFX pull to a series of
        sample files."""

    def test_expected_mixed_rate_edl(self):
        """Compares the EDL output of a mixed-rate VFX pull to a series of
        sample files."""

    def test_expected_mixed_rate_quicktimes(self):
        """Compares the QuickTime output of a mixed-rate VFX pull to a series
        of sample QuickTimes."""

class TestEdlOutput(unittest.TestCase):
    """vfxpull needs to take a valid VFX list and, after grouping shots by
    framerate, string out a valid EDL containing each shot, with
    specified handles."""

    test_csv = os.path.join(PRIVATE_TEST_FILES,
                            'simple_vfx_pull.csv')

    def setUp(self):
        self.vfxlist = [
            {
                'clip_name': '190725_DEEPRANK BULLPEN MEETING.03',
                'reel': 'C042C004_130101_C4PZ',
                'rec_start_tc': '05:04:59:05',
                'rec_end_tc': '05:05:00:05',
                'src_start_tc': '14:07:31:19',
                'src_end_tc': '14:07:32:19',
                'src_framerate': '24',
                'track': '1',
                'sequence_name': 'LG_R5_20200311_V12 mix_VFX FLAT',
                'vfx_id': 'LG_VFX_R5_010',
                'vfx_element': '',
                'vfx_brief': 'SCREEN CLEANUP',
                'vfx_loc_tc': '14:07:32:06',
                'vfx_loc_color': 'MAGENTA',
                'frame_count_start': '1009' }, 
            {
                'clip_name': 'ELIZABETH AND JINGCAO AND TEAM.01',
                'reel': 'C011C001_150831_C4PZ',
                'rec_start_tc': '05:05:05:00',
                'rec_end_tc': '05:05:07:17',
                'src_start_tc': '14:44:36:10',
                'src_end_tc': '14:44:39:03',
                'src_framerate': '24',
                'track': '1',
                'sequence_name': 'LG_R5_20200311_V12 mix_VFX FLAT',
                'vfx_id': 'LG_VFX_R5_020',
                'vfx_element': '',
                'vfx_brief': 'SCREEN CLEANUP',
                'vfx_loc_tc': '14:44:37:11',
                'vfx_loc_color': 'MAGENTA',
                'frame_count_start': '1009' },
            {
                'clip_name': 'ELIZABETH AND JINGCAO AND TEAM.04',
                'reel': 'C011C004_150831_C4PZ',
                'rec_start_tc': '05:05:07:17',
                'rec_end_tc': '05:05:09:20',
                'src_start_tc': '15:06:18:06',
                'src_end_tc': '15:06:20:09',
                'src_framerate': '24',
                'track': '1',
                'sequence_name': 'LG_R5_20200311_V12 mix_VFX FLAT',
                'vfx_id': 'LG_VFX_R5_030',
                'vfx_element': '',
                'vfx_brief': 'SCREEN CLEANUP',
                'vfx_loc_tc': '15:06:19:04',
                'vfx_loc_color': 'MAGENTA',
                'frame_count_start': '1009' }
            ]

    def test_handles(self):
        """If handles are not provided by the VFX list, vfxpull needs to add
        them."""
        pass

    def test_group_by_framerate(self):
        ungrouped_subclips = self.vfxlist

        # get headcount of subclips so we know we aren't missing any
        # at the end
        initial_subclip_count = len(ungrouped_subclips)
        # and make sure we aren't testing an empty list!
        self.assertGreater(initial_subclip_count, 0)

        subclips_by_framerate = vfxpull.group_by_framerate(ungrouped_subclips)

        final_subclip_count = 0
        for fr, subclips in subclips_by_framerate.items():
            for sc in subclips:
                final_subclip_count += 1
                self.assertEqual(fr, sc['src_framerate'])
         
        # make sure we have the same number as subclips as we started with
        self.assertEqual(final_subclip_count, initial_subclip_count)

    def test_create_edl(self):
        """We should have EDLs with the same number of events as subclips."""
        # To-Do: Make this a round trip test
        fr = self.vfxlist[0]['src_framerate']
        pull_list_edl = vfxpull.build_edl(fr, self.vfxlist)
        
        self.assertEqual(len(pull_list_edl), len(self.vfxlist))
        
        next_tc = pull_list_edl.get_start()
        for e, sc in zip(pull_list_edl, self.vfxlist):
            # there should be no filler between clips, and they should
            # not overlap
            self.assertEqual(e.rec_start_tc, next_tc)
            next_tc += (e.src_end_tc - e.src_start_tc)
            # the EDL src timecodes should match the vfxlist timecodes
            self.assertEqual((str(e.src_start_tc), str(e.src_end_tc)),
                             (sc['src_start_tc'], sc['src_end_tc']))
            # the EDL source name should match the vfxlist source name
            self.assertEqual(e.reel, sc['reel'])
        

    def test_write_edl(self):
        pass

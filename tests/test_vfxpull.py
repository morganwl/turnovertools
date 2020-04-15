"""Tests vfxpull script."""

# pylint: goodnames: maxDiff

from hashlib import md5 as checksum
from itertools import zip_longest
import os
import subprocess
import tempfile
import unittest

from timecode import Timecode

from shared_test_setup import get_private_test_files
from shared_test_setup import get_scripts

from scripts import vfxpull
from turnovertools import mediaobjects as mobs
from turnovertools import edl

def get_sample_csv():
    """Get path of sample csv file."""
    sample_csv = get_private_test_files('turnovertools', 'vfx',
                                        'simple_vfx_pull.csv')
    if not os.path.exists(sample_csv):
        raise FileNotFoundError(f'No such file or directory \'{sample_csv}\'')
    return sample_csv

def get_control_sample(*sample):
    """Get path of an arbitrary file in private_control_samples."""
    sample = get_private_test_files('turnovertools',
                                    'vfx',
                                    'control_samples',
                                    'vfxpull', *sample)
    return sample

def get_control_samples():
    """Iterator for all files in private_control_samples."""
    private_control_dir = get_control_sample()
    for sample in sorted(os.listdir(private_control_dir)):
        yield os.path.join(private_control_dir, sample)

def get_control_with_ext(ext):
    """Get path of control file with a given extension."""
    base = get_control_sample('simple_vfx_pull_23976')
    return f'{base}.{ext}'

def inspect_subprocess(obj):
    """Print stdout and stdout of a process."""
    msg = ''
    if hasattr(obj, 'process'):
        process = obj.process
        msg += 'Failure of subprocess \n' + ' '.join(process.args)
        msg += '\n   Standard output:\n'
        msg += process.stdout
        msg += '\n   Standard error:\n'
        msg += process.stderr
    return msg

class TestVFXPullAcceptanceSubprocess(unittest.TestCase):
    """Running vfxpull.py on a simple turnovertools formatted VFX list
    should output a single ALE with subclips for each shot, with
    specified handles, a single EDL with events for each shot, with
    specified handles, and a QuickTime reference video, with burnins,
    matching the pull EDL."""

    args = ()

    @classmethod
    def setUpClass(cls):
        cls.outputdir_obj = tempfile.TemporaryDirectory()
        cls.outputdir = cls.outputdir_obj.name

        cls.backupdir = os.getcwd()
        os.chdir(cls.outputdir)

        tmp_media_db = os.path.join(cls.outputdir, 'tmp_media_db.db')

        # create a temporary environment as a copy of the current
        # environ, then tweak it
        tmp_environ = os.environ.copy()
        tmp_environ.update({
                        'VFX_MEDIA_VOLUMES': get_private_test_files('test_media'),
                        'VFX_MEDIA_DATABASE': tmp_media_db
            })

        cls.process = subprocess.run(('python',
                                      get_scripts('vfxpull.py'),
                                      get_sample_csv(),
                                      cls.outputdir,
                                      *cls.args),
                                     capture_output=True,
                                     env=tmp_environ,
                                     text=True,
                                     check=False)

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.backupdir)
        cls.outputdir_obj.cleanup()
        del cls.outputdir_obj

    def get_output(self, *args):
        """Joins arguments to temporary output path."""
        return os.path.join(self.outputdir, *args)

    def test_process_completion(self):
        """Check that the process completed successfully."""
        output = f'{self.process.stdout}\n{self.process.stderr}'
        self.assertEqual(self.process.returncode, 0, msg=output)

    def test_process_stdout(self):
        """Default arguments of vfxpull should write nothing to stdout."""
        self.assertFalse(self.process.stdout)

    def test_process_stderr(self):
        """There should be no warnings on stderr."""
        self.assertFalse(self.process.stderr)

    def test_expected_ale(self):
        """Compares the ALE output of a simple VFX pull to a sample file."""
        with open(self.get_output('simple_vfx_pull_23976.ale')) as output_ale, \
             open(get_control_with_ext('ale')) as expected_ale:
            for output_line, expected_line in zip(output_ale, expected_ale):
                self.assertEqual(output_line.strip(), expected_line.strip())

    def test_expected_edl(self):
        """Compares the EDL output of a simple VFX pull to a sample file."""
        with open(self.get_output('simple_vfx_pull_23976.edl')) as output_edl, \
             open(get_control_with_ext('edl')) as expected_edl:
            for output_line, expected_line in zip(output_edl, expected_edl):
                self.assertEqual(output_line.strip(), expected_line.strip())

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
                               'simple_vfx_pull.mov'), 'rb') as filehandle:
            chunk = filehandle.read(chunk_size)
            while chunk:
                output_mov_checksum.update(chunk)
                chunk = filehandle.read(chunk_size)
            output_mov_checksum.update(chunk)
        with open(get_control_with_ext('mov'), 'rb') as filehandle:
            chunk = filehandle.read(chunk_size)
            while chunk:
                expected_mov_checksum.update(chunk)
                chunk = filehandle.read(chunk_size)
            expected_mov_checksum.update(chunk)
        self.assertEqual(output_mov_checksum, expected_mov_checksum)

    def test_expected_output_files(self):
        """Checks to see that only the expected files are output."""
        output_files = sorted(os.listdir(self.outputdir))
        for output, expected in zip(output_files, get_control_samples()):
            self.assertEqual(output, os.path.basename(expected))

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


class TestVFXPullAcceptance(unittest.TestCase):
    def setUp(self):
        pass

    def test_edl(self):
        pass

class TestVFXInput(unittest.TestCase):
    def setUp(self):
        pass

    def test_process_input(self):
        with open(get_sample_csv()) as filehandle:
            vfxlist = vfxpull.process_input(filehandle)

class TestALEOutput(unittest.TestCase):
    def setUp(self):
        pass

    def test_vfxlist_to_ale(self):
        vfxlist = list()
        for i in range(5):
            src_start = Timecode(24, '00:01:00:00') * i
            src_end = src_start + 48
            rec_start = Timecode(24, '01:00:00:00') + i * 48
            rec_end = rec_start + 48
            vfxid = f'TEST_{i*10:03d}'
            vfxevent = mobs.VFXEvent.dummy(tape=f'A{i:03d}',
                                           src_start_tc=src_start,
                                           src_end_tc=src_end,
                                           rec_start_tc=rec_start,
                                           rec_end_tc=rec_end,
                                           vfx_id=vfxid)
            vfxlist.append(vfxevent)
        avid_log = vfxpull.vfxlist_to_ale(vfxlist, 24)

class TestEDLOutput(unittest.TestCase):
    """vfxpull needs to take a valid VFX list and, after grouping shots by
    framerate, string out a valid EDL containing each shot, with
    specified handles."""

    def setUp(self):
        self.vfxlist = [
            {
                'clip_name': '190725_DEEPRANK BULLPEN MEETING.03',
                'reel': 'C042C004_130101_C4PZ',
                'rec_framerate': '24',
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
                'frame_count_start': '1009'},
            {
                'clip_name': 'ELIZABETH AND JINGCAO AND TEAM.01',
                'reel': 'C011C001_150831_C4PZ',
                'rec_framerate': '24',
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
                'frame_count_start': '1009'},
            {
                'clip_name': 'ELIZABETH AND JINGCAO AND TEAM.04',
                'reel': 'C011C004_150831_C4PZ',
                'rec_framerate': '24',
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
                'frame_count_start': '1009'}
            ]

    def test_add_handles(self):
        """If handles are not provided by the VFX list, vfxpull needs to add
        them."""
        vfxevent = mobs.VFXEvent.dummy(src_framerate=24,
                                       src_start_tc='01:00:00:08',
                                       src_end_tc='01:00:01:08',
                                       frame_count_start=1009)
        vfxpull.add_handles(vfxevent, 8)
        self.assertEqual(vfxevent.src_start_tc, str('01:00:00:00'))
        self.assertEqual(vfxevent.src_end_tc, str('01:00:01:16'))
        self.assertEqual(vfxevent.frame_count_start, 1001)

    def test_group_by_framerate_vfxevent(self):
        vfxlist = list()
        vfxevent = mobs.VFXEvent.dummy(src_framerate='29.97',
                                       src_start_tc='01:02:23:29',
                                       src_end_tc='01:03:24:00')
        vfxlist.append(vfxevent)
        vfxevent = mobs.VFXEvent.dummy(src_framerate=29.97,
                                       src_start_tc='02:00:01:00',
                                       src_end_tc='02:00:02:00')
        vfxlist.append(vfxevent)
        vfxevent = mobs.VFXEvent.dummy(src_framerate=23.98,
                                       src_start_tc='03:00:01:23',
                                       src_end_tc='03:00:03:00')
        vfxlist.append(vfxevent)
        vfxevent = mobs.VFXEvent.dummy(src_framerate=24,
                                       src_start_tc='04:00:10:12',
                                       src_end_tc='04:00:12:00')
        vfxlist.append(vfxevent)

        initial_vfx_count = len(vfxlist)
        self.assertGreater(initial_vfx_count, 0)

        vfxlist = vfxpull.group_by_framerate(vfxlist)

        final_vfx_count = 0
        for framerate, vfxevents in vfxlist.items():
            for vfxevent in vfxevents:
                final_vfx_count += 1
                self.assertEqual(framerate, str(vfxevent.src_framerate))
        self.assertEqual(final_vfx_count, initial_vfx_count)

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
        pull_list_edl = vfxpull._build_edl_dict(fr, self.vfxlist)

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

    def test_clip_stringout(self):
        """clip_stringout should take a list of clips and string them out end
        to end, without gaps or filler."""
        start_timecode = Timecode(24, '01:00:00:00')
        vfxlist = list()
        for vfx in self.vfxlist:
            vfxlist.append(mobs.VFXEvent(**vfx))
        stringout = vfxpull.clip_stringout(vfxlist, start_timecode)

        next_tc = start_timecode
        for event, vfxevent in zip(stringout, vfxlist):
            self.assertEqual(str(event.rec_start_tc), str(next_tc))
            next_tc += vfxevent.src_duration

    def test_stringout_to_edl(self):
        """stringout_to_edl should accept a list of mobs event, a framerate
        and an optional title, and return an edl.List object."""
        stringout = list()
        title = 'test'
        for i in range(5):
            src_start = Timecode(24, '00:01:00:00') * i
            src_end = src_start + 48
            rec_start = Timecode(24, '01:00:00:00') + i * 48
            rec_end = rec_start + 48
            vfxevent = mobs.VFXEvent.dummy(tape=f'A{i:03d}',
                                           src_start_tc=src_start,
                                           src_end_tc=src_end,
                                           rec_start_tc=rec_start,
                                           rec_end_tc=rec_end)
            stringout.append(vfxevent)
        edit_list = vfxpull.stringout_to_edl(stringout, 24, title)
        self.assertEqual(edit_list.title, title)
        self.assertEqual(str(edit_list.fps), '24')
        self.assertEqual(len(stringout), len(edit_list))
        for edl_event, vfxevent in zip(edit_list, stringout):
            self.assertEqual((edl_event.rec_start_tc, edl_event.rec_end_tc),
                             (vfxevent.rec_start_tc, vfxevent.rec_end_tc))
            self.assertEqual((edl_event.src_start_tc, edl_event.src_end_tc),
                             (vfxevent.src_start_tc, vfxevent.src_end_tc))
            self.assertEqual(edl_event.reel, vfxevent.tape)

    def test_edl_to_str(self):
        """Pass an edl.List event to edl_to_str and compare the output to the
        expected output."""
        edit_list = edl.dummy_list()
        output_edl = vfxpull.edl_to_str(edit_list).split('\n')
        with open(get_control_with_ext('edl')) as expected_edl:
            for output_line, expected_line in zip_longest(output_edl,
                                                          expected_edl):
                self.assertEqual(output_line.strip(), expected_line.strip())

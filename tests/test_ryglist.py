"""Testsuite for xml2ryg2, the second generation clearance processing
tool, per Google Creative Lab specifications."""

# TO-DO: Rewrite tests to more explicitly test the expected inputs and
# outputs of ryglist.

import contextlib
from itertools import zip_longest
import os
import tempfile
import unittest

from shared_test_setup import get_private_test_files, AcceptanceCase
from shared_test_setup import listdir_path
import standards

from scripts import ryglist
from turnovertools import mediaobject, linkfinder, fftools

def get_test_files(*args):
    """Returns files from the private test dir for ryglist."""
    return get_private_test_files('turnovertools', 'ryg', *args)

def get_test_edl():
    """Returns the current test EDL."""
    return get_test_files('LG_R1_20200303_v34.Copy.01.edl')

def get_simple_test_with_ext(ext):
    """Returns a simple test file with the specified extension."""
    basename = get_test_files('ryg_test_reel')
    return f'{basename}.{ext}'

def get_control(*args):
    """Returns files from the control_samples dir for ryglist."""
    return get_test_files('control_samples', *args)

def get_simple_control_with_suffix(suffix):
    """Appends a suffix to the basepath of control samples."""
    basename = get_control('ryg_test_reel')
    return f'{basename}_{suffix}'

class TestRYGListAcceptance(unittest.TestCase, AcceptanceCase):
    """Test end-to-end input and output of ryglist, comparing output of
    given test files to expected outputs. These tests assume that the
    control samples are valid. If the desired output should change,
    new control samples will have to be provided."""

    def setUp(self):
        self.make_tempdir()

    def tearDown(self):
        self.cleanup_tempdir()

    def test_output_csv_edl_only(self):
        """Inputs an EDL and compares the resulting CSV to a control
        sample."""
        # Given a directory as its argument, ryglist should look for
        # needed input files and only run the steps it has inputs
        # for
        self.populate_temp_dir(get_simple_test_with_ext('edl'))

        # redirect RYG's output until we add '-v' or '--quiet' features
        with open(os.devnull, 'w') as null, contextlib.redirect_stdout(null):
            ryglist.main(self.tempdir)

        csvpath = self.get_output(f'{self.basename}.csv')
        csvcontrol = get_simple_control_with_suffix('edl_only.csv')
        self.assertFilesEqual(csvpath, csvcontrol)

    def test_output_csv_with_ale(self):
        """Inputs an EDL and a source ALE and compares the resulting CSV
        to a control sample."""
        self.populate_temp_dir(get_simple_test_with_ext('edl'),
                               get_simple_test_with_ext('ale'))
        with open(os.devnull, 'w') as null, contextlib.redirect_stdout(null):
            ryglist.main(self.tempdir)
        csvpath = self.get_output(f'{self.basename}.csv')
        csvcontrol = get_simple_control_with_suffix('with_ale.csv')
        self.assertFilesEqual(csvpath, csvcontrol)

    def test_output_csv_with_tracker(self):
        """Inputs an EDL, a source ALE and a footage tracker document
        and compares the resulting CSV to a control sample."""
        self.populate_temp_dir(get_simple_test_with_ext('edl'),
                               get_simple_test_with_ext('ale'),
                               get_test_files('lg_footagetracker.csv'))
        with open(os.devnull, 'w') as null, contextlib.redirect_stdout(null):
            ryglist.main(self.tempdir)
        csvpath = self.get_output(f'{self.basename}.csv')
        csvcontrol = get_simple_control_with_suffix('with_tracker.csv')
        self.assertFilesEqual(csvpath, csvcontrol)

    def test_output_frames(self):
        """Inputs an EDL and compares the resulting still frames to
        control samples."""
        self.populate_temp_dir(get_simple_test_with_ext('edl'),
                               get_simple_test_with_ext('mxf'))
        with open(os.devnull, 'w') as null, contextlib.redirect_stdout(null):
            ryglist.main(self.tempdir)
        output_frames = listdir_path(self.get_output(f'{self.basename}_frames'))
        expected_frames = listdir_path(get_simple_control_with_suffix('frames'))
        for output_path, expected_path in zip_longest(output_frames,
                                                      expected_frames):
            self.assertEqual(os.path.basename(output_path),
                             os.path.basename(expected_path))
            with open(output_path, 'rb') as output_frame, \
                 open(expected_path, 'rb') as expected_frame:
                self.assertLess(fftools.mse(output_frame.read(),
                                            expected_frame.read()),
                                10, f'{output_path} and {expected_path}')

    def test_output_videos(self):
        """Inputs an EDL and compares the resulting videos to control
        samples."""


class TestRYGInternals(unittest.TestCase):
    """Test the internal steps of ryglist"""
    def setUp(self):
        self.input = [get_test_edl()]
        with open(os.devnull, 'w') as null, contextlib.redirect_stdout(null):
            self.events = ryglist.events_from_edl(self.input)

    def test_input_edl(self):
        """Confirm that events_from_edl accepts an EDL path and returns
        a list of Event objects (prior generation)."""
        with open(os.devnull, 'w') as null, contextlib.redirect_stdout(null):
            events = ryglist.events_from_edl(self.input)
        for i, event in enumerate(events):
            with self.subTest(i=i):
                self.assertIsInstance(event, mediaobject.Event)

    @unittest.skip('need shorter, faster edl')
    def test_process_events(self):
        """Run process_events and hope it throws no errors."""
        ryglist.process_events(self.events)

#    def test_process_events_getty_still(self):
#        pass

#    def test_process_events_ale(self):
#        pass

#    def test_process_events_footage_tracker(self):
#        pass

#    def test_process_events_qing_art(self):
#        pass

#    def test_process_events_shutterstock_still(self):
#        pass

    @unittest.skip('need shorter, faster edl')
    def test_output_csv(self):
        """Test that a CSV outputs."""
        temp_output = tempfile.NamedTemporaryFile(mode='w+', newline='')
        ryglist.process_events(self.events)
        ryglist.output_csv(self.events, ryglist.Config.OUTPUT_COLUMNS, temp_output)
        temp_output.seek(0)
        for line in temp_output:
            print(line)

    #@unittest.skip('')
    def test_all_matchers(self):
        """Confirm that every event has a tape name after processing."""
        with open(os.devnull, 'w') as null, contextlib.redirect_stdout(null):
            ryglist.process_events(self.events)
        for event in self.events:
            with self.subTest(tape=event.reel):
                self.assertIsNotNone(event.link)

class TestLinkfinderMatchers(unittest.TestCase):
    """Test the Linkfinder matchers that try to populate the link attribute
    of events based on source name, EDL, and getty links."""
    def setUp(self):
        self.matchers = ryglist.Config.MATCHERS

    def test_GETTYIMAGES_520720101_01_LOW_RES(self):
        """Confirm that Linkfinder finds something for a given image."""
        self.assertIsNotNone(linkfinder.process('GETTYIMAGES-520720101-01-LOW_RES', self.matchers))

class TestRYGStandard2(unittest.TestCase, standards.Standard2):
    """Temporary tests to refactor ryglist to be more uniform with the
    the rest of turnovertools."""

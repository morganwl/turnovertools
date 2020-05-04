"""Testsuite for xml2ryg2, the second generation clearance processing
tool, per Google Creative Lab specifications."""

# TO-DO: Rewrite tests to more explicitly test the expected inputs and
# outputs of ryglist.

import contextlib
from itertools import zip_longest
import os
import tempfile
import unittest

from tests.shared_test_setup import get_private_test_files, AcceptanceCase
from tests.shared_test_setup import listdir_path

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
        self.populate_temp_dir(get_simple_test_with_ext('edl'),
                               get_simple_test_with_ext('mxf'))
        with open(os.devnull, 'w') as null, contextlib.redirect_stdout(null):
            ryglist.main(self.tempdir)
        output_dir = self.get_output(f'{self.basename}_video')
        expected_dir = get_simple_control_with_suffix('video')
        output_videos = os.listdir(output_dir)
        expected_videos = os.listdir(expected_dir)
        for output, expected in zip_longest(output_videos,
                                            expected_videos):
            self.assertEqual(output, expected)
            output_path = os.path.join(output_dir, output)
            expected_path = os.path.join(expected_dir, expected)
            self.assertVideoMetadataEqual(output_path, expected_path)
            for error in self.compare_vid_samples(output_path, expected_path):
                self.assertLess(error, 10, f'{output} and {expected}')

@unittest.skip('Proposed new test structure')
class TestRYGListUnits(unittest.TestCase):
    """Test components of ryglist."""

    def setUp(self):
        self.edls = list(get_test_files(f'ryg_three_tracks_V{num}') for num
                         in range(1, 4))

    def test_edl_input(self):
        """Accepts a group of EDLs and returns a mobs.Sequence object
        containing mobs.Event objects. Sequence object mirror EDL
        structure as closely as possible:
          - multiple tracks"""
        # Requires: edl Parser library (EXTERNAL)
        # edl to mobs.Sequence and mobs.Event adapter functions
        # mobs.Sequence and mobs.Event objects

        # spool 3 EDLs, each with 2 non-filler events, with different
        # starting timecodes, into 3 temporary files
        sequence = ryglist.input_edls(self.edls)
        self.assertEqual(len(sequence.tracks), 3)
        self.assertEqual(len(sequence.events), 6)
        self.assertEqual(str(sequence.rec_start_tc), '01:00:00:00')
        self.assertEqual(str(sequence.rec_end_tc), '01:00:04:11')
        self.assertEqual(len(sequence.flatten()), 6)

    def test_update_from_source_table(self):
        """Accepts a mobs.Sequence object and pulls requested metadata
        from a source table for each event."""
        # Requires: mobs.Source object with ability to match to Event
        # Persistent storage for mobs.Source object

    def test_frame_output(self):
        """Accepts a mobs.Sequence object, with an attached media file, and
        exports a single frame for each event in the sequence. Frames could
        be either from the head of each event, or from the middle.

        Extracting an individual frame from a sequence is fairly
        straightforward, but extracting a large number of frames from a
        single sequence seems to be trickier if we want to be time-efficient.

        Profile performance difference between discrete ffmpeg instances
        for each event and extracting a stream of frames from one ffmpeg
        instance."""
        # Requires: mobs.Sequence object with video output capabilities
        # mobs.Event object with src frame to rec frame conversion
        # ability to create multiple frame grabs from single video frame
        sequence = ryglist.input_edls(self.edls)
        sequence.mediapath = get_test_files('ryg_three_tracks.mxf')
        outputdir = tempfile.TemporaryDirectory()
        sequence.output_event_posters(outputdir=outputdir.name, offset='middle')
        for event in sequence.flatten():
            jpeg = f'{event.ref_name}.jpg'
            output_file = os.path.join(outputdir.name, jpeg)
            self.assertTrue(os.path.isfile(output_file))
            self.assertEqual(os.stat(output_file).st_size,
                             os.stat(get_control(jpeg)).st_size)

    def test_export_csv(self):
        """Exports a csv for each event, including requested information
        from source table. CSV row numbers should match frame output
        numbers."""
        # Requires: to_dict() method for mobs.Event

    # rethinking the structure for ryglist
    # abstractly, ryglist has the following functions:
    # - export an image for every shot in an EDL, named according to the shot
    # - export a video for every shot in an EDL, named according to the shot
    # - export a table of all shots in the EDL, collated with additional source
    #   metadata
    # - attempt to gather source metadata from a variety of sources

    # a fundamental flaw of ryglist is that it attempts to collect metadata from
    # raw sources on every run.
    # metadata needs to be stored separately in a sourcetable, which can be
    # updated and maintained as needed.
    # footage_tracker.csv performs some of this function, but we need to do
    # better.
    # we need FileMaker integration.

    # so what are the elements of ryglist?
    # - a sequence parser
    #   - draw from edl library, but convert into our own mobs.Event object
    # - a sequence frame/video extracter
    # - a source table
    #   - source table should have separate utilities for scraping information

    # Development plan:
    # Start by writing a source table module and replacing linkfinder

# to replace
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

# to replace
class TestLinkfinderMatchers(unittest.TestCase):
    """Test the Linkfinder matchers that try to populate the link attribute
    of events based on source name, EDL, and getty links."""
    def setUp(self):
        self.matchers = ryglist.Config.MATCHERS

    def test_GETTYIMAGES_520720101_01_LOW_RES(self):
        """Confirm that Linkfinder finds something for a given image."""
        self.assertIsNotNone(linkfinder.process('GETTYIMAGES-520720101-01-LOW_RES', self.matchers))

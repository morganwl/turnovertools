"""Shared setup and functions for testing turnovertools."""

from itertools import zip_longest
import os
import shutil
import sys
import tempfile

USER_HOME = os.path.expanduser("~")
TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

# pylint: disable=C0413
# we need to insert our package MAIN_DIR into the path before we can perform
# package-level imports
from turnovertools import fftools

def swap_key(dictionary, old, new):
    """Swaps an old key for a new key in a dictionary. If the new key did not
    exist, deletes the old key from the dictionary."""
    temp_val = dictionary.get(new)
    dictionary[new] = dictionary[old]
    if temp_val is None:
        del dictionary[old]
    else:
        dictionary[old] = dictionary[new]

def get_test_files(*args):
    """Returns a path to *args in the test files dir."""
    return os.path.join(TEST_DIR, 'test_files', *args)

def get_scripts(*args):
    """Returns a path to *args in the scripts directory."""
    return os.path.join(MAIN_DIR, 'scripts', *args)

def get_private_test_files(*subpackage):
    """Accepts a subpackage name and returns the private test file directory
    for that package. These are test files stored outside of the project
    directory for total protection against git tracking."""
    return os.path.join(USER_HOME, 'private_test_files', *subpackage)

def listdir_path(*args):
    """Returns the complete path for all files in a directory."""
    basedir = os.path.join(*args)
    for file in os.listdir(basedir):
        yield os.path.join(basedir, file)

class AcceptanceCase:
    """Methods for acceptance tests."""

    def __init__(self):
        self.tempdir_obj = None
        self.tempdir = None
        self.basename = None

    def make_tempdir(self):
        """Creates a temporary directory for input and output."""
        self.tempdir_obj = tempfile.TemporaryDirectory()
        self.tempdir = self.tempdir_obj.name
        self.basename = os.path.basename(self.tempdir)

    def cleanup_tempdir(self):
        """Deletes the temporary directory and all its contents."""
        self.tempdir_obj.cleanup()
        del self.tempdir_obj

    def export_tempdir(self, path):
        """Copies the entire contents of tempdir into a specified path
        that won't be cleaned up by the cleanup_tempdir method."""
        # pylint: disable=W0612
        # need to capture tuple output of os.walk, even if we don't use dirnames
        for dirpath, dirnames, filenames in os.walk(self.tempdir):
            for file in filenames:
                relpath = os.path.relpath(dirpath, self.tempdir)
                destpath = os.path.join(path, relpath)
                if not os.path.isdir(destpath):
                    os.mkdir(destpath)
                shutil.copy(os.path.join(dirpath, file),
                            destpath)

    def populate_temp_dir(self, *files):
        """Copies the given files into the TestCase's temporary
        directory."""
        for file in files:
            shutil.copy(file, self.tempdir)

    def get_output(self, *args):
        """Returns files output into the temp directory."""
        return os.path.join(self.tempdir, *args)

    # pylint: disable=invalid-name
    # unittest uses camel case for its method naming!
    def assertFilesEqual(self, filepath, otherpath):
        """Asserts that two files are equal one line at a time. Accepts
        path-like objects as arguments."""
        # pylint: disable=no-member
        # mix-in class for unittest.TestCase, which has the assert methods
        with open(filepath) as output_file, open(otherpath) as expected_file:
            for output_line, expected_line in zip(output_file, expected_file):
                self.assertEqual(output_line.strip(), expected_line.strip())

    def assertVideoMetadataEqual(self, videopath, otherpath):
        """Compares the metadata of two videofiles using ffprobe, and
        asserts equality one by one."""
        # pylint: disable=no-member
        # mix-in class for unittest.TestCase, which has the assert methods
        video_metadata = fftools.probe_clip(videopath)
        other_metadata = fftools.probe_clip(otherpath)
        # fftools.probe_clip currently uses a junk stub for clip objects,
        # so we do not have a formal way of testing equality
        for attribute in other_metadata.__dict__:
            self.assertEqual(getattr(video_metadata, attribute, None),
                             getattr(other_metadata, attribute, None))

    @staticmethod
    def compare_vid_entire(vid, other, pix_fmt='gray', scale=(960, 540)):
        """Reads in two video files in their entirety, and yields
        a mean-squared error comparison frame by frame. Accepts
        path-like objects as arguments. Optionally specify a different
        pixel format or size for increased detail or increased speed."""
        vid_stream = fftools.interval_stream_frames(
            vid, interval=1, scale=scale, pix_fmt=pix_fmt)
        other_stream = fftools.interval_stream_frames(
            other, interval=1, scale=scale, pix_fmt=pix_fmt)
        for vid_frame, other_frame in zip_longest(vid_stream,
                                                  other_stream):
            yield fftools.mse(vid_frame, other_frame)

    @staticmethod
    def compare_vid_samples(vid, other, pix_fmt='gray', scale=(960, 540),
                            samples=2):
        """Compares specified number of samples from two videos,
        divided equally through the length of the video. Assumes
        videos are of the same length. Takes pathlike objects as
        arguments."""
        duration = float(fftools.probe_clip(other).duration_seconds)
        increment = duration / samples
        for i in range(samples):
            start_seconds = i * increment
            vid_frame = fftools.extract_frame(vid, ss=start_seconds,
                                              inteval=1, scale=scale,
                                              pix_fmt=pix_fmt)
            other_frame = fftools.extract_frame(other, ss=start_seconds,
                                                interval=1, scale=scale,
                                                pix_fmt=pix_fmt)
            yield fftools.mse(vid_frame, other_frame)

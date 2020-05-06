"""Tests the MediaFile class."""

import os
import unittest

import turnovertools.mediaobjects as mobs

def is_jpeg(image):
    """Returns True if a byte string appears to contain a jpeg."""
    if image[:2] != b'\xff\xd8':
        return False
    if image[-2:] != b'\xff\xd9':
        return False
    return True

def get_test_file(*args):
    """Returns args as a path, joined to the base test_files path."""
    return os.path.join('/Volumes', 'LG-Local5-Unmanaged', 'private_test_files',
                        'sourcedb', 'test_media_volume', *args)

class TestMediaFile(unittest.TestCase):
    """MediaFile object should map the metadata for an actual mediafile
    on a drive, and allow reading and writing video and frames from it."""

    def test_from_probe(self):
        """Should be able to create MediaFile by pointing at a filepath."""
        mediafile = mobs.MediaFile.probe(get_test_file('A001C002.mov.V119D8F32AV.mxf'))
        self.assertIsNotNone(mediafile)

    def test_thumbnail(self):
        mediafile = mobs.MediaFile.probe(get_test_file('A001C002.mov.V119D8F32AV.mxf'))
        thumbnail = mediafile.thumbnail()
        self.assertTrue(is_jpeg(thumbnail))

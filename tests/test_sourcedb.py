"""Tests sourcedb, the module for interfacing with an external source
database."""

import os
import subprocess
import unittest

import tests.shared_test_setup

from turnovertools import sourcedb

def get_test_file(*args):
    """Returns args as a path, joined to the base test_files path."""
    return os.path.join('/Volumes', 'LG-Local5-Unmanaged', 'private_test_files',
                        'sourcedb', *args)

class SampleData:
    """Organizes information about test files that need to be accessed
    from the filesystem."""

    def __init__(self, name, path, description=None, inputs=None, outputs=None):
        if inputs is None:
            if outputs is not None:
                inputs = list(outputs.keys())
            else:
                inputs = list()
        if outputs is None:
            outputs = dict()
        if description is None:
            description = ''
        self.name = name
        self.path = path
        self.description = description
        self.inputs = inputs
        self.outputs = outputs

def get_source_db():
    """Returns a SampleData object for a test source database, with
    information about expected values."""
    # pylint: disable=W0201
    reels_with_links = {'A001C001': 'https://www.youtube.com/watch?v=x4xCSVl833I',
                        'A001C002.mov': 'https://www.youtube.com/watch?v=5Q-qzjM3PWc'}
    source_db = SampleData('SourceTableTest.fmp12',
                           path=get_test_file('SourceTableTest.fmp12'),
                           outputs=reels_with_links)
    source_db.kwargs = dict(DATABASE='SourceTableTest')
    source_db.fields = ['clip_name', 'link', 'src_framerate', 'tape',
                        'source_file', 'src_start_tc', 'src_end_tc', 'reel']
    return source_db

class TestReadDatabase(unittest.TestCase):
    """Test that pyodbc interface with FileMaker database is working
    correctly."""

    @classmethod
    def setUpClass(cls):
        cls.test_file = get_source_db()
        subprocess.run(('osascript', '-e',
                        'tell application "FileMaker Pro 18 Advanced" ' +
                        f'to open "{cls.test_file.path}"'))

    def setUp(self):
        self.source_table = sourcedb.SourceTable(sourcedb.connect(**self.test_file.kwargs))

    def tearDown(self):
        self.source_table.close()

    def test_get_reel(self):
        """Inputs a reel name and expects to get a clip object back."""
        for reel in self.test_file.inputs:
            clip = self.source_table[reel]
            self.assertIsNotNone(clip)

    def test_fields(self):
        """Inputs a reel name and expects a clip as a dictionary with
        all the expected fields."""
        clip = self.source_table[self.test_file.inputs[0]]
        for field in self.test_file.fields:
            self.assertIn(field, clip)

    def test_to_clip(self):
        """Should be able to return information as a Mobs.Clip object, instead
        of a dict object."""
        self.fail('This feature not yet implemented.')
        reel = self.test_file.inputs[0]
        fields = self.test_file.fields
        row = self.source_table[reel]
        clip = self.source_table.to_mob(row)
        for field in fields:
            self.assertTrue(hasattr(clip, field))
        self.source_table.as_mobs = True
        clip = self.source_table[reel]
        for field in fields:
            self.assertTrue(hasattr(clip, field))

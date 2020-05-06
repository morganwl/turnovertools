"""Tests sourcedb, the module for interfacing with an external source
database."""

import os
import subprocess
import unittest

import tests.shared_test_setup

from turnovertools.google import GoogleSourceClip
from turnovertools import mediaobjects as mobs
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
    path = get_test_file('SourceTableTest.fmp12')
    source_db = SampleData('SourceTableTest.fmp12',
                           path=path,
                           outputs=reels_with_links)
    source_db.kwargs = dict(database='SourceTableTest', path=path)

    # check fields against mobs standard, but omit a few that we do not
    # need to track in a sources database under any circumstances
    source_db.fields = mobs.SourceClip.standard_attrs()
    source_db.fields.remove('mark_start_tc')
    source_db.fields.remove('mark_end_tc')
    return source_db

def process_running(name):
    """Returns True if a process containing name is running, otherwise
    returns False."""
    try:
        subprocess.run(('pgrep', name), capture_output=True,
                       check=True)
    except subprocess.CalledProcessError:
        return False
    else:
        return True

def db_open(name, app='FileMaker Pro 18 Advanced'):
    """Returns true if a database matching name is open in FileMaker."""
    script = f'tell application "{app}" to get name of every database'
    try:
        result = subprocess.run(('osascript', '-e', script), capture_output=True,
                                check=True)
    except subprocess.CalledProcessError:
        return False
    return name in result.stdout.decode('utf8')

@unittest.skip('Opening and closing the FMP application is too slow for routine testing.')
class TestAppleScript(unittest.TestCase):
    """Test that sourcedb is able to send some basic commands to FileMaker
    through AppleScript (osascript) to make sure it is prepared to receive
    odbc queries."""

    def setUp(self):
        self.test_file = get_source_db()

    def test_open_filemaker(self):
        """Should open FileMaker, and wait until it has launched before
        returning."""
        if process_running('FileMaker'):
            self.fail('FileMaker needs to not be running for this test to work.')
        sourcedb.open_filemaker()
        self.assertTrue(process_running('FileMaker'))
        sourcedb.close_filemaker()

    def test_open_database(self):
        """Should open specified database file and wait until it is
        loaded before returning."""
        if db_open(self.test_file.name):
            self.fail(f'{self.test_file.name} needs not to be open for this ' +
                      'test to work.')
        sourcedb.open_database(self.test_file.path)
        self.assertTrue(db_open(self.test_file.name))
        sourcedb.close_filemaker()

    def test_filemaker_status(self):
        """Should return None if FileMaker is closed, otherwise a list
        of open databases."""
        if process_running('FileMaker'):
            self.assertIsNotNone(sourcedb.filemaker_status())
        else:
            self.assertIsNone(sourcedb.filemaker_status())

class TestReadDatabase(unittest.TestCase):
    """Test that pyodbc interface with FileMaker database is working
    correctly."""

    @classmethod
    def setUpClass(cls):
        cls.test_file = get_source_db()

    @classmethod
    def tearDownClass(cls):
        #sourcedb.close_filemaker()
        pass

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

    def test_image(self):
        """Should be able to read images contained in the database."""
        image = self.source_table.get_blob(self.test_file.inputs[1], 'image', 'JPEG')
        self.assertIsNotNone(image)

    def test_update_container(self):
        """Updates an image into the image field of a source."""
        clip = self.source_table[self.test_file.inputs[0]]
        with open('/Users/morgan/Desktop/source_with_tape_name.png', 'rb') as png:
            self.source_table.update_container(clip['reel'], 'image',
                                               png.read(), 'source_with_tape_name.png')

    def test_insert_image(self):
        """Uses the insert_image method to read and insert an image from a
        filename."""
        clip = self.source_table[self.test_file.inputs[1]]
        self.source_table.insert_image(clip['reel'],
                                       '/Users/morgan/Desktop/source_with_tape_name.png')

    def test_to_clip(self):
        """Should be able to return information as a Mobs.SourceClip object,
        instead of a dict object."""
        #self.fail('This feature not yet implemented.')
        reel = self.test_file.inputs[0]
        fields = self.test_file.fields
        row = self.source_table[reel]
        clip = self.source_table.to_mob(row)
        for field in fields:
            self.assertTrue(hasattr(clip, field))

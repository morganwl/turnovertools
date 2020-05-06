"""Tests the insert_umid script."""

import os
import sqlite3
import unittest

from tests.shared_test_setup import AcceptanceCase
from scripts import insert_umid
from turnovertools import mxfdb, sourcedb
from turnovertools import mediaobjects as mobs

# insert_umid accepts a reel, a record id, and a table name
# if possible, it will update the given record with a umid and a
# thumbnail
# unclear on best approach with multiple umids

def get_test_file(*args):
    """Returns args as a path, joined to the base test_files path."""
    return os.path.join('/Volumes', 'LG-Local5-Unmanaged', 'private_test_files',
                        'sourcedb', *args)

def get_test_files(*args, suffix=None):
    """Yields all files in the path join of args to the base test dir,
    optionally filtering for extension ext."""
    files = os.listdir(get_test_file(*args))
    if suffix:
        files = filter(lambda f: f.endswith(suffix), files)
    for file in files:
        yield file

def chunks(sequence, length):
    """Yields chunks of of given length from a sequence."""
    for i in range(0, len(sequence), length):
        yield sequence[i:i+length]

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

class TestAcceptance(unittest.TestCase, AcceptanceCase):
    """insert_umid accepts a reel, a record id, a fmp file and a table name. If
    possible, it will update the given record with a umid and a
    thumbnail unclear on best approach with multiple umids."""

    def setUp(self):
        self.make_tempdir()
        self.test_file = get_source_db()
        self.source_table = sourcedb.SourceTable(sourcedb.connect(**self.test_file.kwargs))

    def tearDown(self):
        self.cleanup_tempdir()

    def populate_avid_media(self, media, dir_size=None):
        """Copies an iterable list of media into an Avid MediaFiles directory
        in the tempdir, dividing into subfolders folders."""
        dirs = list()
        if not dir_size:
            dir_size = len(media)
        for i, batch in enumerate(chunks(media, dir_size), 1):
            self.populate_temp_dir(*batch,
                                   relpath=('Test Volume', 'Avid MediaFiles',
                                            'MXF', str(i)),
                                   base=get_test_file('test_media_volume'))
            dirs.append(self.get_temp_file('Test Volume', 'Avid MediaFiles',
                                           'MXF', str(i)))
        return dirs

    def test_insert_umid_acceptance(self):
        """Call insert_umid with a record from SourceTableTest and expect
        it to populate record with an image."""
        # set up test media volume
        test_media = list(get_test_files('test_media_volume', suffix='mxf'))
        self.populate_avid_media(test_media)
        db = mxfdb.MediaDatabase(sqlite3.connect(':memory:'),
                                 volumes=[self.get_temp_file('Test Volume')],
                                 quiet=True)
        db.index_all()
        # run insert_umid with second record
        clip = self.source_table[self.test_file.inputs[1]]
        insert_umid.main(clip['source_file'], clip['PrimaryKey'], 'Source',
                         sourcetable=self.source_table, mediadb=db)
        # check contents of image field
        image = self.source_table.get_blob(clip['reel'], 'image', 'JPEG')
        self.assertEqual(image[:2], b'\xff\xd8')

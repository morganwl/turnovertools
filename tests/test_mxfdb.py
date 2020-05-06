"""Tests the mxfdb component."""

import os
import sqlite3
import tempfile
import unittest
from zipfile import ZipFile
import zlib

from tests.shared_test_setup import AcceptanceCase

from turnovertools import mxfdb

def get_test_file(*args):
    """Returns args as a path, joined to the base test_files path."""
    return os.path.join('/Volumes', 'LG-Local5-Unmanaged', 'private_test_files',
                        'mediacopy_helper', *args)

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

class TestFindMedia(unittest.TestCase):
    """We should be able to find media in the database through a variety
    of identifiers, and return information about that media."""

class TestIndexMedia(unittest.TestCase, AcceptanceCase):
    """We should be able to build and maintain an index of all
    Avid MediaFiles directories available. The index should be accurate
    whenever it is called on, but minimize unnecessary work."""

    def setUp(self):
        self.make_tempdir()

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

    def query_umid(self, umid, connection):
        """Queries the MXF database for a path, indexed by umid, by
        performing a union on all of the MXF subdirs."""
        union_buffer = list()
        params = list()
        for mxfdir in self.get_temp_files('Test Volume', 'Avid MediaFiles', 'MXF'):
            table = f'Test_Volume_{mxfdir}'
            union_buffer.append(f'SELECT path FROM {table} WHERE umid=?')
            params.append(umid)
        query = ' UNION '.join(union_buffer)
        result = connection.execute(query, params).fetchone()
        if result:
            return result[0]
        return None

    def test_index_volume(self):
        """Inputs a volume and expects a populated database, with
        a table for each mxf directory."""
        test_files = list(get_test_files('test_media_volume', suffix='mxf'))

        for i, batch in enumerate(chunks(test_files, 3), 1):
            self.populate_temp_dir(*batch,
                                   relpath=('Test Volume', 'Avid MediaFiles',
                                            'MXF', str(i)),
                                   base=get_test_file('test_media_volume'))
        test_volume = self.get_temp_file('Test Volume')

        connection = sqlite3.connect(':memory:')
        db = mxfdb.MediaDatabase(connection, volumes=[test_volume], quiet=True)
        db.index_all()

        for file in test_files:
            umid = mxfdb.probe_umid(get_test_file('test_media_volume', file))
            path = self.query_umid(umid, connection)
            self.assertEqual(os.path.basename(path), file)

    def test_index_repo_volume(self):
        """Inputs a non-Avid volume and expects a recursively populated
        database, with a table for each top-level subfolder."""
        test_media_dir = get_test_file('test_media_volume')
        test_media = list(get_test_files('test_media_volume', suffix='mxf'))
        for i, batch in enumerate(chunks(test_media, 2), 1):
            self.populate_temp_dir(batch[0], relpath=('test_repo', str(i)),
                                   base=test_media_dir)
            self.populate_temp_dir(*batch[1:], relpath=('test_repo', str(i),
                                                        '1'),
                                   base=test_media_dir)
        test_repo = self.get_temp_file('test_repo')
        connection = sqlite3.connect(':memory:')
        db = mxfdb.MediaDatabase(connection, repo_volumes=[test_repo], quiet=True)
        db.index_all()
        for file in test_media:
            umid = mxfdb.probe_umid(get_test_file('test_media_volume', file))
            self.assertIn(umid, db)
            self.assertEqual(db[umid].file, file)

    # TO-DO: Rewrite this for new get_zipped method
    def test_index_zip(self):
        """Inputs a zipfile and expects a list of umids and metadata."""
        zipped_transfer = get_test_file('zipped_transfer.zip')
        self.populate_temp_dir(zipped_transfer, relpath=('test_repo'))

        test_repo = self.get_temp_file('test_repo')
        connection = sqlite3.connect(':memory:')
        db = mxfdb.MediaDatabase(connection, repo_volumes=[test_repo], quiet=True)
        db.index_all()
        # TO-DO: Write actual test!

    # TO-DO: Rewrite this for new get_dir method
    def test_index_dir(self):
        """Inputs a directory and expects an index of umids and
        metadata."""
#        test_media = list(get_test_files('test_media_volume', suffix='mxf'))
#        dirs = self.populate_avid_media(test_media)
#        umids = mxfdb.MediaDatabase.index_dir(None, dirs[0], quiet=True)
#        for file in test_media:
#            path = get_test_file('test_media_volume', file)
#            umid = mxfdb.probe_umid(path)
#            self.assertIn(umid, umids)
#            self.assertEqual(file, umids[umid].file)
#            self.assertTrue(os.path.isfile(umids[umid].path))
#            # just check that the type attribute exists for now
#            self.assertEqual(umids[umid].type, umids[umid].type)

    def test_needs_index(self):
        """Checks to see if DirectoryTable properly recognizes
        directories that do and do not need to be indexed."""
        test_media = list(get_test_files('test_media_volume', suffix='mxf'))
        self.populate_avid_media(test_media)
        test_volume = self.get_temp_file('Test Volume')

        connection = sqlite3.connect(':memory:')
        db = mxfdb.MediaDatabase(connection, volumes=[test_volume], quiet=True)
        db.index_all()

        mxfdir = self.get_temp_file('Test Volume', 'Avid MediaFiles', 'MXF', '1')
        # pylint: disable=W0212
        mxftable = mxfdb.get_tablename(mxfdb.clean_tablename('Test Volume'), mxfdir)
        mtime = os.stat(mxfdir).st_mtime_ns
        self.assertFalse(db.directory.needs_index(mxftable, mtime))

        os.remove(os.path.join(mxfdir, test_media[0]))
        mtime = os.stat(mxfdir).st_mtime_ns
        self.assertTrue(db.directory.needs_index(mxftable, mtime))

    def test_skip_unmodified(self):
        """Indexes a volume, then adds files to one subdirectory, and
        tests to see that only that subdirectory is re-indexed."""
        all_media = list(get_test_files('test_media_volume', suffix='mxf'))
        first_batch = all_media[:-2]
        second_batch = all_media[-2:]
        # populate Test Volume with files from the first batch
        for i, batch in enumerate(chunks(first_batch, 2), 1):
            self.populate_temp_dir(*batch,
                                   relpath=('Test Volume', 'Avid MediaFiles',
                                            'MXF', str(i)),
                                   base=get_test_file('test_media_volume'))
        test_volume = self.get_temp_file('Test Volume')

        connection = sqlite3.connect(':memory:')
        db = mxfdb.MediaDatabase(connection, volumes=[test_volume], quiet=True)
        db.index_all()

        # copy second batch into MXF/1
        self.populate_temp_dir(*second_batch,
                               relpath=('Test Volume', 'Avid MediaFiles',
                                        'MXF', '1'),
                               base=get_test_file('test_media_volume'))
        db.index_all()

    def test_find_umid(self):
        """Indexes a volume and then queries the index by umid."""
        test_media = list(get_test_files('test_media_volume', suffix='mxf'))
        self.populate_avid_media(test_media)
        db = mxfdb.MediaDatabase(sqlite3.connect(':memory:'),
                                 volumes=[self.get_temp_file('Test Volume')],
                                 quiet=True)
        db.index_all()

        for file in test_media:
            umid = mxfdb.probe_umid(os.path.join(get_test_file('test_media_volume'),
                                                 file))
            self.assertIn(umid, db)
            self.assertEqual(db[umid].file, file)

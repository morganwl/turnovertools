"""Database for indexing MXF files by umid."""

import json
import os
import subprocess
import string
import sqlite3
import tempfile
import warnings
from zipfile import ZipFile, BadZipFile
import zlib

def get_media_stream(streams):
    """Returns the metadata for the media stream in an MXF file,
    discarding data streams."""
    found = None
    for stream in streams:
        # skip 'data' streams that provide info about related mxf files
        if stream['codec_type'] == 'data':
            continue
        if found:
            raise UserWarning('Expected only one media stream per MXF.')
        found = stream
    return found

def updir(path, count):
    """Returns the path count directories above path."""
    for _ in range(count):
        path = os.path.dirname(path)
    return path

def validate_table(table):
    """Table can only accept alphanumeric characters and _ (underscore).
    Otherwise, will raise ValueError."""
    val_table = table.replace('-', '')
    val_table = val_table.replace('_', '')
    if not val_table.isalnum():
        raise ValueError(f"Invalid table name: '{table}'. Check volume name" +\
                         "for non-standard characters, or improve path " + \
                         "sanitization methods.")

def clean_tablename(name):
    """Accepts a name, and returns with whitespace replaced by
    underscores and any other non-alphanumeric characters removed."""
    no_whitespace = str.maketrans(string.whitespace + '.' + '-',
                                  '_'*(len(string.whitespace)+2))
    name = name.translate(no_whitespace)
    return ''.join(char for char in name if char.isalnum() or char == '_')

def get_tablename(vol, subdir):
    """Gets basename of subdir, cleans it, and then returns table name
    in naming convention. Assumes that vol has already been cleaned."""
    subdir = clean_tablename(os.path.basename(subdir))
    return f'{vol}_{subdir}'

def get_mxfdir(vol):
    """Returns the path to an Avid MediaFiles MXF top-level dir for a
    given volume."""
    return os.path.join(vol, 'Avid MediaFiles', 'MXF')

def get_subdirs(path, index_zips=False):
    for entry in os.listdir(path):
        subdir = os.path.join(path, entry)
        if os.path.isdir(subdir) or (subdir.endswith('.zip') and index_zips):
            yield subdir

def is_mediafile(fname):
    """Returns True if a filename matches an indexable MXF filename."""
    if fname.startswith('__MACOSX'):
        return False
    if os.path.basename(fname).startswith('.'):
        return False
    return fname.endswith('.mxf')

# pylint: disable=R0903
class Probe:
    """Probes a mediafile and presents common metadata as attributes."""

    def __init__(self, filepath):
        """Runs ffprobe on filepath at instantiation."""
        args = ['ffprobe', '-of', 'json', '-show_format', '-show_streams', filepath]
        probe = subprocess.run(args, capture_output=True, check=False)
        self.data = json.loads(probe.stdout.decode('utf8'))
        self.stream = get_media_stream(self.data['streams'])
        self.umid = self.stream['tags']['file_package_umid'].lower()
        self.type = self.stream['codec_type']
        self.name = self.data['format']['tags']['material_package_name']
        self.mediatype = self.type
        self.path = filepath
        self.file = os.path.basename(filepath)

    def set_altpath(self, altpath):
        """Change filename and path based on a path other than one used
        for probe."""
        self.file = os.path.basename(altpath)
        self.path = altpath


class MediaFile:
    """Metadata for an Avid MediaFile."""

    def __init__(self, umid=None, file=None, path=None, name=None,
                 mediatype=None):
        self.umid = umid
        self.file = file
        self.path = path
        self.name = name
        self.mediatype = mediatype


class Progress:
    """Displays progress of indexing files."""

    base_quiet = False
    progress_bar_length = 80

    def __init__(self, quiet=None):
        if quiet is None:
            quiet = self.base_quiet
        self.quiet = quiet
        self.progress_per_file = 0
        self.accumulated = 0
        self.progress = 0

    @classmethod
    def set_quiet(cls, quiet=True):
        """Sets the class level default quiet."""
        cls.base_quiet = quiet

    def message(self, msg):
        """Prints a message, based on quiet settings."""
        if not self.quiet:
            print(msg)

    def set_length(self, length):
        """Configures the progress object based on the number of objects
        needing to be processed."""
        self.progress = 0
        if length == 0:
            self.progress_per_file = self.progress_bar_length
            self.increment()
            return
        self.progress_per_file = self.progress_bar_length / length

    def increment(self, units=1):
        """Increments the progress counter by one or more units of work,
        and updates the displayed progress bar if appropriate."""
        self.accumulated += units * self.progress_per_file
        accumulated = self.accumulated + units * self.progress_per_file
        if accumulated >= 1:
            display_units = int(accumulated)
            self.accumulated = accumulated - display_units
            self.progress += display_units
            self.display(display_units)

    def flush(self):
        """Flushes the progress bar, filling it, and then printing a
        a new line."""
        if self.progress < self.progress_bar_length:
            self.display(self.progress_bar_length - self.progress)
        if not self.quiet:
            print('')

    def display(self, units):
        """Updates the progress bar by the specified number of units."""
        if not self.quiet:
            print('.'*units, sep='', end='', flush=True)

class MediaDatabase:
    """Creates and maintains an index of every single Avid-accessible .mxf
    file on a specified group of volumes.

    MXF files are indexed by their umid as retrieved by ffprobe of the
    ffmpeg suite. The string is uppercase, apart from the hexadecimal
    prefix '0x'. See
    https://en.wikipedia.org/wiki/Unique_Material_Identifier for
    further details."""

    def __init__(self, conn=None, volumes=None, repo_volumes=None, quiet=False):
        self.conn = conn
        self.volumes = volumes
        self.repo_volumes = repo_volumes
        self.quiet = quiet
        Progress.base_quiet = quiet
        self.mxf_tables = list()
        self.directory = DirectoryTable(conn)
        self.create_directory()

    def close(self):
        """Closes the connection to the database."""
        self.conn.commit()
        self.conn.close()

    def create_directory(self):
        """Creates required database tables, if they don't already
        exist."""
        self.directory.create_table()

    @staticmethod
    def index_files(files, progress=None):    # files is an iterator
        """Iterates over files and returns an indexed dictionary.
        Optionally triggers a pre-initialized Progress object."""
        mediafiles = dict()
        for file, altpath in files:
            if progress:
                progress.increment()
            try:
                mediafile = Probe(file)
            except TypeError as e:
                msg = (f'{e}: Could not find valid media stream for {file}')
                warnings.warn(msg, UserWarning)
                continue
            if altpath:
                mediafile.set_altpath(altpath)
            mediafiles[mediafile.umid] = mediafile
        return mediafiles

    @staticmethod
    def get_dir(path, progress=None):
        """Yields all .mxf files in the top-level of a directory and
        optionally initializes a progress bar."""
        files = os.listdir(path)
        mxf = list(os.path.join(path, fname) for fname in files
                   if is_mediafile(fname))
        if progress:
            progress.set_length(len(mxf))
        for file in mxf:
            yield file, None

    @staticmethod
    def get_dir_recursive(path, progress=None, index_zips=True):
        """Recursively yeilds all .mxf files in a directory and optionally
        initializes a progress bar."""
        mxf = list()
        for dirpath, _, fnames in os.walk(path):
            for fname in fnames:
                if is_mediafile(fname):
                    mxf.append(os.path.join(dirpath, fname))
                if fname.endswith('.zip') and index_zips:
                    yield from MediaDatabase.get_zipped(os.path.join(dirpath, fname),
                                                        progress=progress)
                    progress.flush()
        if progress:
            progress.set_length(len(mxf))
        for file in mxf:
            yield file, None

    @staticmethod
    def get_zipped(path, progress=None):
        """Yields all .mxf files in a zipfile by extracting them to a
        tempfile. Optionally initializes a progress bar."""
        #breakpoint()
        with ZipFile(path) as ziphandle:
            zipped_mxf = list(file for file in ziphandle.namelist()
                              if is_mediafile(file))
            if progress:
                progress.set_length(len(zipped_mxf))
            for entry in zipped_mxf:
                try:
                    mxf = ziphandle.open(entry)
                except BadZipFile as e:
                    msg = f'Could not open {entry} in {path}'
                    warnings.warn(msg, e)
                    continue
                with tempfile.NamedTemporaryFile(suffix='.mxf') as file:
                    file.write(mxf.read())
                    yield file.name, os.path.join(path, entry)
                mxf.close()

    def get_repo(self, path, progress=None):
        """Evaluates path and either gets files from zip or recursively
        from directory."""
        if path.endswith('.zip'):
            yield from self.get_zipped(path, progress)
        yield from self.get_dir_recursive(path, progress)

    def _index_zip(self, zippath, quiet=None):
        umids = dict()
        with ZipFile(zippath) as zipped:
            for file in (file for file in zipped.namelist()
                         if file.endswith('.mxf')):
                if os.path.basename(file).startswith('.'):
                    continue
                try:
                    zmxf = zipped.open(file)
                except BadZipFile:
                    msg = f'Could not open {file} in {zippath}'
                    warnings.warn(msg)
                    continue
                with tempfile.NamedTemporaryFile(suffix='.mxf') as mxf:
                    mxf.write(zmxf.read())
                    #print(mxf.name, '--', file, sep='\n')
                    #breakpoint()
                    try:
                        mediafile = Probe(mxf.name)
                    except:
                        warnings.warn(f'Could not find valid media stream for {mxf}', RuntimeWarning)
                    mediafile.file = file
                    mediafile.path = os.path.join(zippath, file)
                    umids[mediafile.umid] = mediafile
                zmxf.close()
        return umids

    @staticmethod
    def __path_to_tablename(mxfdir):
        """Converts a subfolder path to format Volume_Subfolder to match
        table naming format."""
        mxfdir = mxfdir.strip('/')               # trailing slashes will
                                                 # confuse os.path functions
        subfolder = os.path.basename(mxfdir)
        vol = os.path.basename(updir(mxfdir, 3)) # get the basename dir containing
                                                 # Avid MediaFiles/MXF
        table = f'{vol}_{subfolder}'.replace(' ', '_')
        return table.replace('-', '_').replace('.', '_').replace('’', '')
    ####

    def drop(self, table):
        """Drops the table 'table'. Suppresses exception if table does
        not exist."""
        validate_table(table)
        with self.conn as c:
            try:
                c.execute(f'DROP TABLE {table}')
            except sqlite3.OperationalError:
                c.rollback()
        # remove table from mxf_tables

    def index_volume(self, volname, topdir, file_getter, index_zips=False):
        """Indexes a volume, creating a new table for each top-level
        subdirectory, and skipping those which have not changed since
        their last indexing. Topdir does not have to be the root of the
        volume."""
        #breakpoint()
        if not os.path.isdir(topdir):
            return  # skip if there is no media dir on the volume
        volname = clean_tablename(volname)
        subdirs = get_subdirs(topdir, index_zips)
        for subdir in subdirs:
            progress = Progress()
            table = get_tablename(volname, subdir)
            mxftable = MXFTable(table, self.conn)
            self.mxf_tables.append(mxftable)

            modified_time = os.stat(subdir).st_mtime_ns
            # skip subdir if it hasn't been modified since last index
            print
            if table in self.directory and int(self.directory[table]) >= modified_time:
                progress.message(f'{subdir} up to date. Skipping.')
                continue

            # drop old version of subdir table, if it exists
            self.drop(table)
            progress.message(f'Indexing {subdir} ({table})')
            # get files to index with file_getter provided by caller
            files = file_getter(subdir, progress)
            # create a new table and register it with the current modified_time
            mxftable.create_with(self.index_files(files))
            progress.flush()
            self.directory[table] = modified_time


    # this method needs major cleanup!
    def _index_repo_volume(self, vol):
        """Recursively indexes all mxf files in a volume, creating tables
        by subdirectories of the root level of the tree."""
        subdirs = (path for path in (os.path.join(vol, entry)
                                     for entry in os.listdir(vol))
                   if os.path.isdir(path))
        for mxfdir in subdirs:
            table = f'{os.path.basename(vol)}_{os.path.basename(mxfdir)}'.replace(' ', '_')
            table = table.replace('-', '_')
            mxftable = MXFTable(table, self.conn)
            self.mxf_tables.append(mxftable)

            mtime = os.stat(mxfdir).st_mtime_ns
            if table in self.directory and self.directory[table] == mtime:
                if not self.quiet:
                    print('Skipping', mxfdir)
                continue
            if not self.quiet:
                print('Indexing', mxfdir)
            self.drop(table)
            mxftable.create_with(self.recurse_index_dir(mxfdir))
            self.directory[table] = mtime
        subzips = (path for path in (os.path.join(vol, entry)
                                     for entry in os.listdir(vol))
                   if path.endswith('.zip'))
        for mxfdir in subzips:
            table = f'{os.path.basename(vol)}_{os.path.basename(mxfdir)}'.replace(' ', '_')
            table = table.replace('.', '_')
            table = table.replace('-', '_')
            print(table)
            mxftable = MXFTable(table, self.conn)
            self.mxf_tables.append(mxftable)
            mtime = os.stat(mxfdir).st_mtime_ns
            if table in self.directory and self.directory[table] == mtime:
                if not self.quiet:
                    print('Skipping', mxfdir)
                continue
            if not self.quiet:
                print('Indexing', mxfdir)
            self.drop(table)
            mxftable.create_with(self.index_zip(mxfdir))
            self.directory[table] = mtime

    def index_all(self, volumes=None):
        """Index a list of volumes. If none are specified, indexes all
        volumes specified at object instantiation. If that value is None,
        uses contents of '/Volumes' directory."""
        if volumes is None:
            volumes = self.volumes
        if volumes is None and self.repo_volumes is None:
            volumes = (os.path.join('/Volumes', vol) for vol in os.listdir('/Volumes'))
        if volumes:
            for vol in volumes:
                self.index_volume(os.path.basename(vol), get_mxfdir(vol),
                                  self.get_dir)
        if self.repo_volumes:
            for vol in self.repo_volumes:
                self.index_volume(os.path.basename(vol),
                                  vol, self.get_repo, index_zips=True)

    def _query_mxf_tables(self, umid):
        union_buffer = list()
        params = list()
        for table in (mxftable.table for mxftable in self.mxf_tables):
            union_buffer.append(f'SELECT * FROM {table} WHERE umid=?')
            params.append(umid)
        query = ' UNION '.join(union_buffer)
        with self.conn as c:
            result = c.execute(query, params).fetchone()
        if result:
            return result
        return None

    def __getitem__(self, key):
        result = self._query_mxf_tables(key)
        if result is None:
            raise KeyError
        return MediaFile(**self._columns_to_dict(result))

    def __contains__(self, key):
        if self._query_mxf_tables(key):
            return True
        return False

    @staticmethod
    def _columns_to_dict(sequence):
        """Converts a sequence of values, ordered in table order, to
        a dictionary matching column names."""
        umid, file, path, name, mediatype = sequence
        row = dict(umid=umid, file=file, path=path, name=name,
                   mediatype=mediatype)
        return row

class MXFTable():
    """An SQL table containing metadata, indexed by umid."""
    SCHEMA = '''CREATE TABLE IF NOT EXISTS {}
    ( umid TEXT PRIMARY KEY, file TEXT, path TEXT,
    name TEXT, mediatype TEXT );'''

    #def __init__(self, conn=None):
    def __init__(self, table, conn):
        validate_table(table)
        self.table = table
        self.conn = conn

    def create(self):
        """Validates and then creates the table."""
        validate_table(self.table)
        with self.conn as c:
            c.execute(self.SCHEMA.format(self.table))

    def create_with(self, umids):
        """Creates the table and then inserts a collection of metadata
        into it. umids should be a dictionary of Probe objects or
        dictionaries."""
        self.create()
        with self.conn as c:
            for umid, metadata in umids.items():
                c.execute(f'INSERT INTO {self.table} VALUES (?, ?, ?, ?, ?)',
                          (umid, metadata.file, metadata.path, metadata.name,
                           metadata.type))

#    @staticmethod
#    def _path_to_tablename(mxfdir):
#        """Converts a subfolder path to format Volume_Subfolder to match
#        table naming format."""
#        mxfdir = mxfdir.strip('/')               # trailing slashes will
#                                                 # confuse os.path functions
#        subfolder = os.path.basename(mxfdir)
#        vol = os.path.basename(updir(mxfdir, 3)) # get the basename dir containing
#                                                 # Avid MediaFiles/MXF
#        return f'{vol}_{subfolder}'.replace(' ', '_')

#    def update(self, mxfdir, items):
#        """Updates the MXFtable with a dictionary of Probe objects."""
#        table = self._path_to_tablename(mxfdir)
#        for umid, metadata in items:
#            with self.conn as c:
#                c.execute(f'INSERT INTO {table} VALUES (?, ?, ?, ?, ?)',
#                          (umid, metadata.file, metadata.path,
#                           metadata.name, metadata.type))

#    def delete_dir(self, path):
#        """Delete all entries for a specific MXF subfolder."""
#        with self.conn as c:
#            c.execute('DELETE FROM Mxf WHERE path=?', (path,))

    def __getitem__(self, key):
        with self.conn as c:
            r = c.execute('SELECT filename, path FROM Mxf WHERE umid=?;', (key,)).fetchone()
        if r is None:
            raise KeyError
        return r

    def __setitem__(self, key, val):
        filename, path = val
        if key in self:
            with self.conn as c:
                c.execute('UPDATE f{self.table} SET filename=?, path=? WHERE umid = ?;',
                          (filename, path, key))
        else:
            with self.conn as c:
                c.execute('INSERT INTO f{self.table} VALUES (?, ?, ?);', (key, filename, path))

    def __contains__(self, key):
        with self.conn as c:
            if c.execute(f'SELECT umid from {self.table} WHERE umid=?;', (key,)).fetchone():
                return True
        return False

    def get(self, key):
        pass

class DirectoryTable:
    """Access class for SQL table that tracks the modification time of
    every MXFTable ever seen in the database."""
    SCHEMA = '''CREATE TABLE IF NOT EXISTS Directory (mxftable TEXT PRIMARY KEY, mtime INT);'''

    def __init__(self, conn=None):
        self.conn = conn

    def create_table(self):
        """Creates the table if it does not exist."""
        with self.conn as c:
            c.execute(self.SCHEMA)

    def update(self, items):
        """Updates the table with new values."""
        for key, val in items:
            self[key] = val

    def needs_index(self, mxftable, mtime):
        """Returns true if mxftable is either not in the DirectoryTable,
        or if mtime is more recent than last indexing."""
        if mxftable not in self:
            return True
        if self[mxftable] < mtime:
            return True
        return False

    def __getitem__(self, key):
        """Returns the mtime for a given mxftable."""
        with self.conn as c:
            result = c.execute('SELECT mtime FROM Directory WHERE mxftable=?;', (key,)).fetchone()
        if result is None:
            raise KeyError
        return int(result[0])

    def __setitem__(self, key, val):
        if key in self:
            self._update(key, val)
        else:
            self._insert(key, val)

    def __contains__(self, key):
        with self.conn as c:
            if c.execute('SELECT mxftable FROM Directory WHERE mxftable=?;', (key,)).fetchone():
                return True
        return False

    def _update(self, key, val):
        with self.conn as c:
            c.execute('UPDATE Directory SET mtime=? WHERE mxftable=?;', (key, val))

    def _insert(self, key, val):
        with self.conn as c:
            c.execute('INSERT INTO Directory VALUES (?, ?);', (key, val))


def probe_umid(fname):
    """Probes a file with ffprobe and returns the file_package_umid
    for the active media stream."""
    args = ['ffprobe', '-of', 'json', '-show_format', '-show_streams', fname]
    probe = subprocess.run(args, capture_output=True, check=False)
    data = json.loads(probe.stdout.decode('utf8'))
    streams = data['streams']
    # each mxf file contains data streams describing related mxf files,
    # and one actual media stream. we want the umid for that media stream.
    for stream in streams:
        # skip 'data' streams that provide info about related mxf files
        if stream['codec_type'] == 'data':
            continue
        return stream['tags']['file_package_umid'].lower()

def open(db_file, volumes=None, repo_volumes=None, quiet=False):
    """Opens a new MediaDatabase stored in db_file."""
    connection = sqlite3.connect(db_file)
    db = MediaDatabase(connection, volumes=volumes, repo_volumes=repo_volumes,
                       quiet=quiet)
    db.index_all()
    return db

if __name__ == '__main__':
    MediaDatabase(sqlite3.connect('mxfdb.db')).index_all()

"""Interface for interfacing with a FileMaker Pro database in order to
lookup Source information."""

import logging
import os
import subprocess
import string
import time

import pyodbc

from turnovertools import mediaobjects as mobs
from turnovertools.config import Config

FILEMAKER_DRIVER = '/Library/ODBC/FileMaker ODBC.bundle/Contents/MacOS/fmodbc.so'

def sanitize_name(name):
    """Remove questionable characters from a name string."""
    newchars = list()
    name, ext = os.path.splitext(name)
    for c in name:
        if c in string.whitespace and newchars and newchars[-1] != ' ':
            newchars.append(' ')
        elif c in string.ascii_letters:
            newchars.append(c)
        elif c in string.digits:
            newchars.append(c)
    return ''.join(newchars) + ext

def connect(database=None, path=None, **kwargs):
    """Creates a connection to a Database and properly configures the
    utf-8 encoding."""
    status = filemaker_status()
    if status is None:
        open_filemaker()
    if database not in filemaker_status() and path is not None:
        open_database(path)
    odbc_args = dict(DRIVER=FILEMAKER_DRIVER,
                     DATABASE=database,
                     CHARSET='utf-8',
                     SERVER='localhost',
                     UID='Python')
    odbc_args.update(kwargs)
    connection = pyodbc.connect(**odbc_args)
    connection.setencoding('utf-8')
    connection.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
    SourceTable.prior_status = status
    return connection

def filemaker_status(app=None):
    """If FileMaker is not open, returns None. Otherwise returns a list
    of all open databases."""
    if app is None:
        app = Config.FILEMAKER_APPLICATION
    try:
        subprocess.run(('pgrep', app), capture_output=True,
                       check=True)
    except subprocess.CalledProcessError:
        return None
    else:
        script = f'tell application "{app}" to get name of every database'
        result = subprocess.run(('osascript', '-e', script), capture_output=True,
                                check=False)
        if b'execution error' in result.stderr:
            return []
        return list(db.strip() for db in result.stdout.decode('utf8').split(','))

def open_filemaker(app=None, refresh=.1):
    """Uses AppleScript to open FileMaker. Optionally provide name of
    FileMaker application, or use value stored in Config."""
    if app is None:
        app = Config.FILEMAKER_APPLICATION
    script = (f'tell application "{app}" to activate\n' +
              'tell application "Finder" to set visible of application ' +
              f'process "{app}" to false')
    subprocess.run(('osascript', '-e', script), capture_output=True, check=False)
    while filemaker_status(app) is None:
        time.sleep(refresh)

def open_database(path, app=None, refresh=.1):
    """Uses AppleScript to open a FileMaker database and waits until it
    is open to return."""
    if app is None:
        app = Config.FILEMAKER_APPLICATION
    database = os.path.basename(path)
    script = (f'tell application "{app}" to open "{path}"\n' +
              'tell application "Finder" to set visible of application ' +
              f'process "{app}" to false')
    subprocess.run(('osascript', '-e', script), capture_output=True, check=False)
    while database not in filemaker_status():
        time.sleep(refresh)

def close_filemaker(app=None, refresh=.1):
    """Uses AppleScript to quit FileMaker application, and waits until
    the application has closed before returning."""
    if app is None:
        app = Config.FILEMAKER_APPLICATION
    script = f'tell application "{app}" to quit'
    try:
        subprocess.run(('osascript', '-e', script), capture_output=True, check=True)
    except subprocess.CalledProcessError:
        return None
    while filemaker_status() is not None:
        time.sleep(refresh)

class SourceTable:
    """Accesses a Sources table in a FileMaker Pro database."""

    prior_status = None

    def __init__(self, connection):
        self.connection = connection
        self._fields = list(self._get_fields())

    def close(self):
        """Closes the connection. Further attempts to access the database
        will raise exceptions."""
        self.connection.close()
        if self.prior_status is None:
            close_filemaker()

    def to_mob(self, record):
        """Accepts a record as a dictionary or row and returns a
        mobs.Clip object."""
        if isinstance(record, pyodbc.Row):
            record = self._row_to_dict(record)
        return mobs.SourceClip(**record)

    def update(self, reel, field, val, pk=False):
        """Changes the value of field in an an existing element
        in the table."""
        keyfield = 'PrimaryKey' if pk else 'reel'
        with self.connection as c:
            c.execute(f'UPDATE Source SET {field}=? WHERE {keyfield} = ?',
                      (val, reel))

    def update_container(self, key, field, val, put_as, pk=False):
        """Updates a container object with an AS {filename} keyword. If
        pk is set, uses PrimaryKey to index records instead of the default
        reel."""
        keyfield = 'PrimaryKey' if pk else 'reel'
        with self.connection as c:
            sql = f"UPDATE Source SET {field}=? AS '{sanitize_name(put_as)}' " +\
                  f"WHERE {keyfield}=?"
            logging.info("EXECUTED QUERY: %s with key %s", sql, key)
            c.execute(sql, (val, key))

    def insert_image(self, reel, filepath):
        """Reads a binary file from filename and puts it in the image
        field of a source, using the filename for the AS keyword."""
        name = os.path.basename(filepath)
        with open(filepath, 'rb') as image:
            self.update_container(reel, 'image', image.read(), name)

    def get_blob(self, reel, field, blobtype):
        """Reads a binary string from a Container field."""
        with self.connection as c:
            result = c.execute(f"SELECT GetAs({field}, '{blobtype}') " +
                               "FROM Source WHERE reel=?", (reel,)).fetchone()
        return result[0]

    def get_pk(self, key):
        """Get record by specific PrimaryKey instead of reel. Reels should
        be unique, but this might be necessary in some circumstances."""
        with self.connection as c:
            query = c.execute(f'SELECT * FROM Source WHERE PrimaryKey=?', (key,))
            result = query.fetchone()
        return self._row_to_dict(result)

    def _get_fields(self):
        with self.connection as c:
            query = c.execute('SELECT FieldName FROM FileMaker_Fields ' +
                              'WHERE TableName=?', ('Source',))
            fields = query.fetchall()
        for row in fields:
            yield row[0]

    def __getitem__(self, reel):
        with self.connection as c:
            query = c.execute(f'SELECT * FROM Source WHERE reel=?', (reel,))
            rows = query.fetchmany(2)
        if len(rows) > 1:
            raise KeyError(f'Multiple sources returned for {reel}')
        return self._row_to_dict(rows[0])

    def _row_to_dict(self, row):
        record = dict()
        for field, val in zip(self._fields, row):
            record[field] = val
        return record

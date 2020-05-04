"""Interface for interfacing with a FileMaker Pro database in order to
lookup Source information."""

import pyodbc

FILEMAKER_DRIVER = '/Library/ODBC/FileMaker ODBC.bundle/Contents/MacOS/fmodbc.so'

def connect(**kwargs):
    """Creates a connection to a Database and properly configures the
    utf-8 encoding."""
    odbc_args = dict(DRIVER=FILEMAKER_DRIVER,
                     CHARSET='utf-8',
                     SERVER='localhost',
                     UID='Python')
    odbc_args.update(kwargs)
    connection = pyodbc.connect(**odbc_args)
    connection.setencoding('utf-8')
    connection.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
    return connection

class SourceTable:
    """Accesses a Sources table in a FileMaker Pro database."""

    def __init__(self, connection):
        self.connection = connection
        self._fields = list(self._get_fields())

    def close(self):
        """Closes the connection. Further attempts to access the database
        will raise exceptions."""
        self.connection.close()

    def to_mob(self, record):
        """Accepts a record as a dictionary or row and returns a
        mobs.Clip object."""
        if isinstance(record, pyodbc.Row):
            record = self._row_to_dict(record)

    def update(self, reel, field, val):
        """Changes the value of field in an an existing element
        in the table."""
        with self.connection as c:
            c.execute('UPDATE ALE_Import SET ?=? WHERE reel = ?', (field,
                                                                   val, reel))

    def _get_fields(self):
        with self.connection as c:
            query = c.execute('SELECT FieldName FROM FileMaker_Fields ' +
                              'WHERE TableName=?', ('Source',))
            fields = query.fetchall()
        for row in fields:
            yield row[0]

    def __getitem__(self, key):
        with self.connection as c:
            query = c.execute(f'SELECT * FROM Source WHERE reel=?', (key,))
            rows = query.fetchmany(2)
        if len(rows) > 1:
            raise KeyError('Multiple sources returned for {key}')
        return self._row_to_dict(rows[0])

    def _row_to_dict(self, row):
        record = dict()
        for field, val in zip(self._fields, row):
            record[field] = val
        return record

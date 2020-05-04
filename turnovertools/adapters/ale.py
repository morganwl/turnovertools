"""Input and output to ALE."""

from collections import OrderedDict
import csv
import os

from turnovertools.config import Config

def read_translation_table(filehandle):
    """Read a translation table from a csv with mob attribute names in
    first column and AvidLog field names in second column."""
    reader = csv.reader(filehandle)
    rows = list(row for row in reader)
    return dict((adapter, mob) for mob, adapter in rows)

def translate(old, translation_table):
    """Returns a new dictionary with keys based on translation_table."""
    result = dict()
    for field, val in old.items():
        if field in translation_table:
            result[translation_table[field]] = val
        else:
            result[field] = val
    return result

def translate_fields(old, translation_table):
    """Returns a new list of field names based on a translation table."""
    result = list()
    for field in old:
        if field in translation_table:
            result.append(translation_table[field])
        else:
            result.append(field)
    return result

with open(os.path.join(os.path.dirname(__file__), 'translation_tables', 'ale.csv')) as table_file:
    TRANSLATION_TABLE = read_translation_table(table_file)

def parse_token(filehandle, token):
    """Iterates through filehandle until token found. If value found after
    token, returns it."""
    for line in filehandle:
        line = line.strip()
        if line.startswith(token):
            if len(line) > len(token):
                return line.rsplit('\t', 1)[1]
            return None
    msg = f'Expected {token} in {filehandle}, but found EOF'
    raise ValueError(msg)

class AvidLog:
    """Avid Log Exchange input and output."""

    def __init__(self, delim='TABS', video_format='1080', audio_format='48khz',
                 framerate=Config.DEFAULT_FRAMERATE, rows=None, columns=None):
        self.delim = delim
        self.video_format = video_format
        self.audio_format = audio_format
        self.framerate = framerate
        if rows is None:
            rows = list()
        self.rows = list(Row(row) for row in rows)
        if columns is None:
            if rows:
                columns = self.columns_from_rows(rows)
            else:
                columns = list()
        self.columns = columns

    @classmethod
    def parse(cls, filehandle):
        """Constructor method that parses an ALE file and returns an
        AvidLog object."""
        filehandle.reconfigure(errors='ignore')
        parse_token(filehandle, 'Heading')
        delim = parse_token(filehandle, 'FIELD_DELIM')
        video_format = parse_token(filehandle, 'VIDEO_FORMAT')
        audio_format = parse_token(filehandle, 'AUDIO_FORMAT')
        framerate = parse_token(filehandle, 'FPS')
        parse_token(filehandle, 'Column')
        columns = next(filehandle).strip().split('\t')
        parse_token(filehandle, 'Data')
        rows = list()
        for line in filehandle:
            line = line.strip('\n')
            rows.append(OrderedDict(zip(columns, line.split('\t'))))
        return cls(delim=delim, video_format=video_format,
                   audio_format=audio_format, framerate=framerate,
                   columns=columns, rows=rows)

    @classmethod
    def columns_from_rows(cls, rows):
        """Returns all keys found in a list of rows."""
        return list()

    def write_csv(self, filehandle, columns=None,
                  translation_table=None):
        """Writes contents as a mobs formatted csv."""
        if translation_table is None:
            translation_table = TRANSLATION_TABLE
        if columns is None:
            columns = translate_fields(self.columns, translation_table)
        writer = csv.DictWriter(filehandle, columns, extrasaction='ignore')
        writer.writeheader()
        for row in self:
            writer.writerow(translate(row, translation_table))

    def __str__(self):
        """Returns a valid ALE file as a string."""

    def __getitem__(self, key):
        return self.rows[key]

    def __setitem__(self, key, row):
        if not hasattr(row, 'keys') and not callable(row.keys):
            msg = f'Expected a dict-like object, not {type(row)}'
            raise ValueError(msg)
        self.rows[key] = Row(row)

    def __len__(self):
        return len(self.rows)

    def __delitem__(self, key):
        del self.rows[key]

    def insert(self, index, val):
        """Not implemented."""
        raise NotImplementedError()

    def append(self, row):
        """Appends a row to the ALE. Raises exception if row is not
        dict-like."""
        if not hasattr(row, 'keys') and not callable(row.keys):
            msg = f'Expected a dict-like object, not {type(row)}'
            raise ValueError(msg)
        self.rows.append(Row(row))

class Row(OrderedDict):
    """OrderedDict child class with some AvidLog specific features."""

    def to_mobs_dict(self):
        """Remaps dictionary keys to mobs attribute names. Leaves
        attributes not defined by mobs unchanged."""
        mobs_dict = dict()
        for field, val in self.items():
            if field in TRANSLATION_TABLE:
                mobs_dict[TRANSLATION_TABLE[field]] = val
            else:
                mobs_dict[field] = val
        return mobs_dict

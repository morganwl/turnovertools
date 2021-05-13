"""Inputs a csv file and outputs a valid ALE file (Avid Log Exchange)
for import into Avid Media Composer.

usage: csv2ale.py <input.csv> [output file] [columns]

The optional argument [columns] is a comma-separated list of ALE
column names, in the order they appear in the incoming csv file. These
names have no relation to original field names used to make the
csv. (In fact, csv2ale.py does not currently support files with headers.)

If no columns are specified, the default is defined by the constant
ALE_COLUMNS. This is a deprecated legacy feature; the columns argument
is highly recommended.

If no output file is specified, the path of the inputfile, plus
'.ale' is used.

TO-DO: Detect header row in .csv. (FileMaker does not output csvs
       with header row, but other workflows do.) csv header should
       be overridden if columns are specified on command line.
TO-DO: Use mediaobject classes for additional functionality and
       error checking.

"""

from collections import namedtuple
import csv
import sys

ALE_HEADER_LINES = [
    'Heading',
    'FIELD_DELIM\tTABS',
    'VIDEO_FORMAT\t1080',
    'FILM_FORMAT\t35mm, 4 perf',
    'AUDIO_FORMAT\t48khz',
    'FPS\t23.976',
    '',
    'Column']
ALE_COLUMNS = ['Name', 'Tape', 'Source File', 'Frame Count Start', 'Start', 'End', 'Tracks', 'VFX_ID', 'Mark IN', 'Mark OUT', 'Auxiliary TC1', 'Notes for Edit', 'Batch', 'Date']
CUSTOM_COLUMN_MAX_LENGTH = 250 # custom columns with more than the
                               # allowed number of characters will
                               # crash Avid on import

def read_csv(inputfile):
    rows = list()
    with open(inputfile, newline='') as fh:
        reader = csv.reader(fh)
        for row in reader:
            # truncate columns that exceed max-length
            for i, col in enumerate(row):
                if len(col) > CUSTOM_COLUMN_MAX_LENGTH:
                    row[i] = col[:CUSTOM_COLUMN_MAX_LENGTH - 3] + '...'
            rows.append(row)
    return rows

def main(inputfile, outputfile=None, columns=None):
    pulls = read_csv(inputfile)
    if outputfile is None:
        outputfile = inputfile + '.ale'
    if columns is None:
        columns = ALE_COLUMNS
    else:
        columns = columns.split(',')
    with open(outputfile, 'w') as fh:
        fh.write('\n'.join(ALE_HEADER_LINES))
        fh.write('\n')
        fh.write('\t'.join(columns))
        fh.write('\nData\n')
        for clip in pulls:
            fh.write('\t'.join(clip))
            fh.write('\n')

if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])


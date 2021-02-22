from collections import namedtuple
import csv
import sys

ALERow = namedtuple('ALERow', ('Name', 'Tape', 'Frame_Count_Start', 'Start', 'End', 'Tracks', 'VFX_ID'))

ALE_HEADER_LINES = [
    'Heading',
    'FIELD_DELIM\tTABS',
    'VIDEO_FORMAT\t1080',
    'FILM_FORMAT\t35mm, 4 perf',
    'AUDIO_FORMAT\t48khz',
    'FPS\t23.976',
    '',
    'Column']
ALE_COLUMN_ROWS = ['Name', 'Tape', 'Frame Count Start', 'Start', 'End', 'Tracks', 'VFX_ID']

def read_csv(inputfile):
    rows = list()
    with open(inputfile, newline='') as fh:
        reader = csv.reader(fh)
        for row in reader:
            rows.append(ALERow(*row))
    return rows


def main(inputfile, outputfile=None):
    pulls = read_csv(inputfile)
    if outputfile is None:
        outputfile = inputfile + '.ale'
    with open(outputfile, 'w') as fh:
        fh.write('\n'.join(ALE_HEADER_LINES))
        fh.write('\n')
        fh.write('\t'.join(ALE_COLUMN_ROWS))
        fh.write('\nData\n')
        for clip in pulls:
            fh.write('\t'.join(clip))
            fh.write('\n')

if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])


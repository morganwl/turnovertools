"""Parse vendor e-mail and create submission csv for importing into
FileMaker."""

from dateutil.parser import parse

import csv
import os
import sys

SHOW_PREFIX = 'GOH_'
SHOT_TAG_LENGTH = 12

def main(inputfile):
    submission = list()
    basename = os.path.splitext(os.path.basename(inputfile))[0].replace(' ', '')
    date = parse(basename.split('_')[-1])
    batch = '_'.join(basename.split('_')[0:2])
    outputfile = f'{date.year}{date.month:02}{date.day:02}_{batch}.csv'
    outputpath = os.path.join(os.path.dirname(inputfile), outputfile)
    with open(inputfile) as fh:
        while fh:
            line = next(fh)
            if line.startswith('Content-Type: text/plain;'):
                break
        while fh:
            line = next(fh)
            if line.startswith(SHOW_PREFIX) and ' ' not in line:
                break
        while fh:
            if not line.startswith(SHOW_PREFIX):
                break
            shot = line[len(SHOW_PREFIX):len(SHOW_PREFIX)+SHOT_TAG_LENGTH]
            submission.append((line.strip(), shot, 'DPX', '', '', '', ''))
            line = next(fh)
    with open(outputpath, 'wt') as fh:
        writer = csv.writer(fh)
        writer.writerow(('Filename', 'Shot', 'Format', 'First Frame', 'Last Frame', 'Duration', 'Notes'))
        for row in submission:
            writer.writerow(row)

if __name__ == '__main__':
    main(sys.argv[1])

"""
Quick hack of a script to parse EDLs made from conform for VFX
database, because 3rd party EDL library does not support them.
"""

import csv
import os
import sys

COLUMNS = ('reel', 'src_start_tc', 'src_end_tc', 'rec_start_tc',
           'rec_end_tc', 'clip_name', 'sequence_name')

def get_line_token(lines, startswith):
    while lines:
        line = next(lines)
        if line.startswith(startswith):
            return line[len(startswith):].strip()

def split_event(line):
    tokens = list(filter(None, line.split(' '))) # split by whitespace
    return (tokens[1], *tokens[-4:])

        
def main(inputfile):
    rows = list()
    with open(inputfile) as fh:
        title = get_line_token(fh, 'TITLE: ')
        fcm = get_line_token(fh, 'FCM: ')
        print(title)
        print(fcm)
        while fh:
            event = None
            clipname = None
            while fh:
                try:
                    line = next(fh)
                except StopIteration:
                    break
                if line == '\n':
                    continue
                if line.startswith('*'):
                    break
                event = split_event(line.strip())
            while fh:
                if line.startswith('* FROM CLIP NAME: '):
                    clipname =  line[len('* FROM CLIP NAME: '):].strip()
                if not line.startswith('*'):
                    break
                try:
                    line = next(fh)
                except StopIteration:
                    break
            if not event:
                break
            rows.append((*event, clipname, title))
    with open(inputfile + '.csv', 'wt') as fh:
        writer = csv.writer(fh)
        writer.writerow(COLUMNS)
        for row in rows:
            writer.writerow(row)
                
if __name__ == '__main__':
    main(sys.argv[1])

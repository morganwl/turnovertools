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
    """Consumes iterator until it finds a line starting with startswith,
    and returns that line."""
    while lines:
        line = next(lines)
        if line.startswith(startswith):
            return line[len(startswith):].strip()

def split_event(line):
    """Splits a line into tokens divided by one or more spaces."""
    tokens = list(filter(None, line.split(' '))) # split by whitespace
    return (tokens[1], *tokens[-4:])

        
def main(inputfile):
    rows = list()
    with open(inputfile) as fh:
        # grab EDL header info
        title = get_line_token(fh, 'TITLE: ')
        fcm = get_line_token(fh, 'FCM: ')

        # main event loop
        while fh:
            event = None
            clipname = None

            # process event rows until first comment
            # last row of composite events will clobber first row (good)
            # this won't work on an EDL that has no comments!
            while fh:
                try:
                    line = next(fh)
                except StopIteration:
                    break
                if line == '\n':
                    continue
                # exit once we start comments
                if line.startswith('*'):
                    break
                event = split_event(line.strip())

            # loop over comments
            while fh:
                if line.startswith('* FROM CLIP NAME: '):
                    clipname =  line[len('* FROM CLIP NAME: '):].strip()
                # we usually want the name of the clip  fading up from black
                if line.startswith('* TO CLIP NAME: '):
                    clipname = line[len('* TO CLIP NAME: '):].strip()
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

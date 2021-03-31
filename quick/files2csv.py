"""
Reads a directory and creates a csv of all entries with extension '.mov',
containing the filename, src_start_tc and src_end_tc.

usage: files2csv.py [directory]

This csv is intended to be used for importing VFX submissions into a VFX
database when the vendor has not provided their own submission csv.
"""

import csv
import os
import sys

from turnovertools.mediaobjects import MediaFile

ROWS = ('Filename', 'src_start_tc', 'src_end_tc')

def get_videos(dir):
    files = os.scandir(dir)
    for file in files:
        if file.name.endswith('.mov'):
            yield (file.name, file.path)
    files.close()

def video_to_row(filename, filepath):
    clip = MediaFile.probe(filepath)
    return(filename, clip.src_start_tc, clip.src_end_tc)
    
def main(inputdir):
    if inputdir.endswith('/'):
        inputdir = inputdir[:-1]
    output = os.path.join(inputdir,
                         os.path.basename(inputdir) + '.csv')
    with open(output, 'wt', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(ROWS)
        for filename, filepath in get_videos(inputdir):
            writer.writerow(video_to_row(filename, filepath))
    print(output)

if __name__ == '__main__':
    main(sys.argv[1])

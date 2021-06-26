"""
Reads a directory and creates a csv of all entries with extension '.mov'
or '.mp4', containing the source filename, the absolute path,
src_start_tc and src_end_tc.

This csv is intended to be used for importing stock into a VFX database.
"""

import csv
import os
import sys

from turnovertools.mediaobjects import MediaFile, Timecode

ROWS = ('src_file', 'src_path', 'src_start_tc', 'src_end_tc',
        'source_type', 'src_framerate')

def get_videos(dir):
    files = os.scandir(dir)
    for file in files:
        # Replace with a lookup table of media file extensions, or bypass file
        # extension altogether and do a trial probe (slower)
        if file.name.endswith('.mov') or file.name.endswith('.mp4') or file.name.endswith('.mxf'):
            yield (file.name, file.path)
    files.close()

def video_to_row(filename, filepath):
    clip = MediaFile.probe(filepath)
    clip.src_framerate = Timecode.normalize_framerate(clip.src_framerate)
    return(filename, os.path.abspath(filepath), clip.src_start_tc,
            clip.src_end_tc, 'Stock', clip.src_framerate)
    
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

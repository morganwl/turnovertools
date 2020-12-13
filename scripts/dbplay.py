#!/usr/bin/env python3

"""
dbplay.py

Play a segment of a video file, based on information stored in a database.
"""

import subprocess
import sys

from turnovertools import mediaobjects as mobs

def main(start_tc, end_tc, mediapath):
    mediafile = mobs.MediaFile.probe(mediapath)
    mediafile.play(start_tc, end_tc)

if __name__ == '__main__':
    main(*sys.argv[1:])

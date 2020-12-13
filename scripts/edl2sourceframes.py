#!/usr/bin/env python3

import os
import sys

from turnovertools import edl
import turnovertools.mediaobjects as mobs
from turnovertools import mxfdb
from turnovertools.config import Config

def remove_filler(events):
    """Removes events with no source information from the provided list."""
    for event in events:
        if event.reel is None:
            events.remove(event)
            continue

def sort_by_tc(events):
    """Sorts events by their rec_start_tc."""
    events.sort(key=lambda e: (e.rec_start_tc.frames, e.track))
    return events

def get_thumbnail(reel, mediadb):
    umids = list(mediadb.get_umids(reel, 'video'))
    if not umids:
        return
    mediafile = mobs.MediaFile.probe(umids[0].path)
    return mediafile.thumbnail()

def main(inputfile, outputdir, mediadb=None):
    if mediadb is None:
        mediadb = mxfdb.open(Config.MXFDB)
    elif isinstance(mxfdb, str):
        mediadb = mxfdb.open(mxfdb)

    if os.path.isdir(inputfile):
        dirname = os.path.basename(inputfile)
        basepath = os.path.abspath(inputfile)
        inputfile = list()
        for file in os.listdir(basepath):
            if file.lower().endswith('.edl'):
                inputfile.append(os.path.join(basepath, file))
    else:
        inputfile = [inputfile]

    events = edl.events_from_edl(inputfile)
    remove_filler(events)
    sort_by_tc(events)
    for i, event in enumerate(events):
        reel = event.reel
        frame = get_thumbnail(reel, mediadb)
        if frame is None:
            reel = reel.rsplit('.', 1)[0]
            frame = get_thumbnail(reel, mediadb)
            if frame is None:
                print(f'No image found for {reel}')
                continue
        outname = f'{i:03}_{reel}.jpg'
        with open(os.path.join(outputdir, outname), 'wb') as outfile:
            outfile.write(frame)

if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])

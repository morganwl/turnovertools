"""
Accepts an EDL or folder containing EDLs and attempts to output a
reference frame from the Avid source media for every event in the EDL.

WARNING: Requires access to corresponding Avid media and uses a
turnovertools media database, which could take several hours to build
for first usage.

usage: edl2sourceframes.py <edl file|edl directory> <output directory> [mediadb]

If the first argument is a directory, edl2sourceframes will operate on
every file in the directory (non-recursively) with a .edl extension.
"""

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
    """Queries mediadb for a mediafile matching reel, returning a
    corresponding thumbnail, or None if no matching mediafile is
    found."""
    umids = list(mediadb.get_umids(reel, 'video'))
    if not umids:
        return None
    mediafile = mobs.MediaFile.probe(umids[0].path)
    return mediafile.thumbnail()

def main(inputfile, outputdir, mediadb=None):
    """Accepts either a single EDL or a directory containing
    EDLs. Iterates through every event in each EDL and outputs a
    reference thumbnail from the referenced source media to
    outputdir. mediadb can be an mxfdb object or a path to an mxfdb
    database file. If no mediadb is provided, will open (or generate)
    a db in the location specified by Config.MXFDB."""
    if mediadb is None:
        mediadb = mxfdb.open(Config.MXFDB)
    elif isinstance(mxfdb, str):
        mediadb = mxfdb.open(mxfdb)

    if os.path.isdir(inputfile):
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

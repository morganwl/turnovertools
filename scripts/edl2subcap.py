import os
import sys

from turnovertools import edl
from turnovertools.subcap import Subcap

def change_ext(filename, ext):
    """Replaces the extension of filename with ext."""
    return os.path.splitext(filename)[0] + ext

def remove_filler(events):
    """Removes events with no source information from the provided list."""
    for event in events:
        if event.reel is None:
            events.remove(event)
            continue
def make_subcaps(events):
    """Creates a Subcap (Avid caption) object for each vfxevent with
    the vfx_id and vfx_brief."""
    subcaps = list()
    for event in events:
        subcaps.append(Subcap(event.rec_start_tc, event.rec_end_tc,
                              event.clip_name))
    return subcaps


def main(inputfile, outputfile=None):
    events = edl.events_from_edl([inputfile])
    print(events)
    #remove_filler(events)
    subcaps = make_subcaps(events)
    if outputfile is None:
        outputfile = change_ext(inputfile, '_subcap.txt')
    Subcap.write(outputfile, subcaps)

if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])

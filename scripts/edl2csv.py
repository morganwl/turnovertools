#!/usr/bin/env python3

"""
Creates a csv of events and vfxevents from a group of EDLs (assuming
that the EDLs represent separate tracks of the same sequence.) Meant
for input into a FileMaker database.
"""

import csv
import os
import re
import sys
import tempfile

#from timecode import Timecode

#from turnovertools.edlobjects import EDLEvent
from turnovertools import edl
from turnovertools.subcap import Subcap

# migrate to config.Config for configuration options
class Config:
    OUTPUT_COLUMNS = ['clip_name', 'reel', 'rec_start_tc',
                      'rec_end_tc', 'src_start_tc', 'src_end_tc',
                      'src_framerate', 'track', 'sequence_name', 'vfx_id',
                      'vfx_element', 'vfx_brief', 'vfx_loc_tc',
                      'vfx_loc_color', 'frame_count_start', 'asc_sop',
                      'asc_sat']

def capitalize_sentences(s):
    s = s.lower()
    buffer = list()
    start = 0
    for i, char in enumerate(s):
        if char in ('.', '?', '!'):
            buffer.append(s[start:i+1].capitalize())
            start = i+1
    buffer.append(s[start:].capitalize())
    return ''.join(buffer)
    
def change_ext(filename, ext):
    """Replaces the extension of filename with ext."""
    return os.path.splitext(filename)[0] + ext

def sort_by_tc(events):
    """Sorts events by their rec_start_tc."""
    events.sort(key=lambda e: (e.rec_start_tc.frames, e.track))
    return events

def fn_to_track(fn):
    """Parses an EDL filename into a track number, assuming that the
    EDLs are named with a convention of Sequence_V[track_number].edl"""
    return change_ext(fn, '').rsplit('_', 1)[1].replace('V', '')

def remove_filler(events):
    """Removes events with no source information from the provided list."""
    for event in events:
        if event.reel is None:
            events.remove(event)
            continue

# TO-DO: specify frame_count_start in configuration object
# TO-DO: more rigorous locator parsing at object level
def read_vfx_locators(events):
    """
    Parses vfx information out of locators on events and intro
    attributes of the edl object.

    Locators should be of the format:
    vfx=[vfx_id]=[vfx_element]=[vfx_brief]

    If not all 3 fields are present, populates fields in the following
    priority: vfx_id, vfx_brief, vfx_element.

    Also sets event.vfx_loc_tc based on the corresponding src_tc and sets
    vfx_loc_color. event.frame_count_start is set to a default of 1009.
    """
    for event in events:
        for loc in event.locators:
            # changed in 0.0.7, use regex to parse locator, to allow
            # for EDL variations
            match = re.match(
                '\*\s*LOC:\s+(\d\d:\d\d:\d\d:\d\d)\s+(\w+)\s+(.*)',
                loc)

            tc, color, comment = match.group(1, 2, 3)

            if comment.startswith('VFX='):
                fields = comment.split('=')
                # Allow for missing fields in the middle by starting
                # with the vfx_id at the front of the string and then
                # popping decreasingly important fields from the back
                fields.pop(0)
                event.vfx_id = fields.pop(0).strip()
                event.vfx_brief = ''
                event.vfx_element = ''
                # TODO: Configurable frame_count_start
                event.frame_count_start = 1017
                if fields:
                    event.vfx_brief = capitalize_sentences(fields.pop().strip())
                if fields:
                    event.vfx_element = fields.pop().strip()
                event.vfx_loc_tc = event.src_tc_at(tc)
                event.vfx_loc_color = color.strip()

def make_subcaps(events):
    """Creates a Subcap (Avid caption) object for each vfxevent with
    the vfx_id and vfx_brief."""
    subcaps = list()
    for event in events:
        if hasattr(event, 'vfx_id'):
            subcaps.append(Subcap(event.rec_start_tc, event.rec_end_tc,
                                  f'{event.vfx_id}:    {event.vfx_brief}'))
    return subcaps

# TO-DO: use DictWriter and mobs.to_dict() method
# TO-DO: use mobs object to specify default columns
def output_csv(events, columns, csvfile):
    """Outputs processed vfxevents to the filehandle csvfile."""
    writer = csv.writer(csvfile)
    writer.writerow(columns)

    for event in events:
        row = []
        for col in columns:
            if hasattr(event, col.lower()):
                val = getattr(event, col.lower(), None)
            else:
                val = event.get_custom(col)
            row.append(val)
        writer.writerow(row)

# TO-DO: migrate filename parsing to interface.py
# TO-DO: use mobs.events instead of EDLEvents
def main(inputfile, outputfile=None):
    output_columns = Config.OUTPUT_COLUMNS
    if os.path.isdir(inputfile):
        dirname = os.path.basename(inputfile)
        basepath = os.path.abspath(inputfile)
        inputfile = list()
        if outputfile is None:
            outputfile = os.path.join(basepath, dirname + '.csv')
        for file in os.listdir(basepath):
            if file.lower().endswith('.edl'):
                inputfile.append(os.path.join(basepath, file))
    else:
        inputfile = [inputfile]

    # optionally create a temporary output file *which will not be
    # deleted on exit. This is meant for a FileMaker script that will
    # delete the file after reading it.
    if outputfile == ':temp':
        # tmpdir = os.path.expanduser('~')
        with tempfile.NamedTemporaryFile(mode='wt', suffix='.csv',
                                         delete=False) as temp:
            outputfile = temp.name
        print(os.path.realpath(outputfile))

    events = edl.events_from_edl(inputfile)
    remove_filler(events)
    sort_by_tc(events)
    read_vfx_locators(events)
    subcaps = make_subcaps(events)

    if outputfile is None:
        outputfile = change_ext(inputfile[0], '.csv')
    with open(outputfile, 'wt', newline='') as csvfile:
        output_csv(events, output_columns, csvfile)

    Subcap.write(change_ext(outputfile, '_subcap.txt'), subcaps)

if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])

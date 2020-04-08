#!/usr/bin/env python3

import csv
import os
import sys
import tempfile

# import edl
from timecode import Timecode

from turnovertools.edlobjects import EDLEvent
from turnovertools import csvobjects, edl
from turnovertools.subcap import Subcap

class Config(object):
    OUTPUT_COLUMNS = ['clip_name', 'reel', 'rec_start_tc',
                      'rec_end_tc', 'src_start_tc', 'src_end_tc',
                      'src_framerate', 'track', 'sequence_name', 'vfx_id',
                      'vfx_element', 'vfx_brief', 'vfx_loc_tc',
                      'vfx_loc_color', 'frame_count_start']

def change_ext(filename, ext):
    return os.path.splitext(filename)[0] + ext

def sort_by_tc(events):
    events.sort(key=lambda e: (e.rec_start_tc.frames, e.track))
    return events

def fn_to_track(fn):
    return change_ext(fn, '').rsplit('_', 1)[1].replace('V', '')

def remove_filler(events):
    for e in events:
        if e.reel is None:
            events.remove(e)
            continue

def read_vfx_locators(events):
    for e in events:
        for l in e.locators:
            tc = l[7:18]
            color, comment = l[19:].split(' ', 1)
            if comment.startswith('VFX='):
                fields = comment.split('=')
                # Allow for missing fields in the middle by starting
                # with the vfx_id at the front of the string and then
                # popping decreasingly important fields from the back
                fields.pop(0)
                e.vfx_id = fields.pop(0).strip()
                e.vfx_brief = ''
                e.vfx_element = ''
                e.frame_count_start = 1009
                if fields:
                    e.vfx_brief = fields.pop().strip()
                if fields:
                    e.vfx_element = fields.pop().strip()
                e.vfx_loc_tc = e.src_tc_at(tc)
                e.vfx_loc_color = color.strip()

def make_subcaps(events):
    subcaps = list()
    for e in events:
        if hasattr(e, 'vfx_id'):
            subcaps.append(Subcap(e.rec_start_tc, e.rec_end_tc,
                                  f'{e.vfx_id}:    {e.vfx_brief}'))
    return subcaps

def output_csv(events, columns, csvfile):
    writer = csv.writer(csvfile)

    writer.writerow(columns)

    for e in events:
        row = []
        for col in columns:
            if hasattr(e, col.lower()):
                val = getattr(e, col.lower(), None)
            else:
                val = e.get_custom(col)
            row.append(val)
        writer.writerow(row)

def main(inputfile, outputfile=None, **kwargs):
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
        inputfile = [ inputfile ]

    # optionally create a temporary output file *which will not be
    # deleted on exit. This is meant for a FileMaker script that will
    # delete the file after reading it.
    if outputfile == ':temp':
        # tmpdir = os.path.expanduser('~')
        with tempfile.NamedTemporaryFile(mode='wt', suffix='.csv',
                                         delete=False) as tf:
            outputfile = tf.name
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
    main(*sys.argv[1:])

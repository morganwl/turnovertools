#!/usr/bin/env python3

import csv
import os
import sys

import edl
from timecode import Timecode

from turnovertools.edlobjects import EDLEvent
from turnovertools import csvobjects
from turnovertools.subcap import Subcap

class Config(object):
    OUTPUT_COLUMNS = ['clip_name', 'reel', 'rec_start_tc',
                      'rec_end_tc', 'src_start_tc', 'src_end_tc',
                      'track', 'sequence_name', 'vfx_id',
                      'vfx_element', 'vfx_brief', 'vfx_loc_tc',
                      'vfx_loc_color']

def change_ext(filename, ext):
    return os.path.splitext(filename)[0] + ext

def sort_by_tc(events):
    events.sort(key=lambda e: (e.rec_start_tc.frames, e.track))
    return events

def events_from_edl(edl_files):
    tmp_events = list()
    seq_start = Timecode('23.98', '23:59:59:23')
    edit_lists = list()
    for file in edl_files:
        edit_list = import_edl(file)
        edit_list.filename = os.path.basename(file)
        if edit_list.get_start().frames < seq_start.frames:
            seq_start = edit_list.get_start()
        edit_lists.append(edit_list)
    events = list()
    for l in edit_lists:
        for e in l:
            if e.has_transition():
                # to the best I can tell, the event before
                # has_transition is a dummy event
                del events[-1]
                add_transition_out(events[-1], e)
                add_transition_in(e, e.next_event)
                continue
            events.append(EDLEvent(seq_start, e))
            e.sequence_name = l.title
            e.track = fn_to_track(l.filename)
    return events

def add_transition_out(e, tr):
    if e is None or e.rec_end_tc != tr.rec_start_tc:
        # skip instances where the prior event does not exist or does
        # not precede the transition (like if transition is first
        # event in a track)
        return
    e.src_end_tc += int(e.speed * tr.incoming_transition_duration())
    e.rec_end_tc = tr.rec_end_tc

def add_transition_in(tr, e):
    if e is None or tr.rec_end_tc != e.rec_start_tc:
        return
    speed = e.src_length() / e.rec_length()
    e.src_start_tc -= int(speed * tr.incoming_transition_duration())
    e.rec_start_tc = tr.rec_start_tc

def get_src_end_with_transition(e, tr_end_tc):
    fade_duration = e

def fn_to_track(fn):
    return change_ext(fn, '').rsplit('_', 1)[1].replace('V', '')

def import_edl(edl_file):
    parser = edl.Parser('23.98')
    with open(edl_file) as fh:
        edit_list = parser.parse(fh)
    return edit_list

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
                print(e.src_start_tc.framerate)
                fields = comment.split('=')
                # Allow for missing fields in the middle by starting
                # with the vfx_id at the front of the string and then
                # popping decreasingly important fields from the back
                fields.pop(0)
                e.vfx_id = fields.pop(0)
                e.vfx_brief = ''
                e.vfx_element = ''
                if fields:
                    e.vfx_brief = fields.pop()
                if fields:
                    e.vfx_element = fields.pop()
                e.vfx_loc_tc = e.src_tc_at(tc)
                e.vfx_loc_color = color

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
        outputfile = os.path.join(basepath, dirname + '.csv')
        for file in os.listdir(basepath):
            if file.lower().endswith('.edl'):
                inputfile.append(os.path.join(basepath, file))
    else:
        inputfile = [ inputfile ]
    
    events = events_from_edl(inputfile)
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
    main(sys.argv[1])

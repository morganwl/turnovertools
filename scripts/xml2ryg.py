#!/usr/bin/env python3

import csv
from itertools import chain
import os
import re
import sys

from turnovertools import xmlobjects

class Config(object):
    OUTPUT_COLUMNS = ['event_num', 'clip_name', 'reel', 'Link',
                      'Footage Type', 'Footage Source', 'rec_start_tc',
                      'rec_end_tc', 'src_start_tc', 'src_end_tc']
    
##
# Event processing functions
def process_events(events):
    for e in events:
        if e.reel is None:
            events.remove(e)
            continue
        guess_metadata(e)
    for i, e in enumerate(events):
        set_event_num(e, i+1)
    return events

def remove_filler(e):
    if e.reel is None:
        return None
    return e

def compare_existing(e):
    # we don't have a great way to track changes between turnovers,
    # because we don't have any way of indexing the shots
    # our best bet is probably to do a mixture of a source table, with
    # changes to that, and a changelist style comparison
    raise NotImplementedError()

def guess_metadata(e):
    if e.get_custom('Link') is None:
        e.set_custom('Link', guess_link(e))
    return e

def set_event_num(e, i):
    e.event_num = str(i)

##
# Guessing functions

def guess_link(e):
    if e.reel and re.search('^[A-Z][0-9]{3}C[0-9]{3}', e.reel):
        return 'PRODUCTION'

##
# Setup functions

def events_from_xml(xmlpath):
    sequence = xmlobjects.XMLSequence.fromfile(xmlpath)[0]
    events = []
    for t in sequence:
        events.extend(t.events)
    return events

def sort_by_tc(events):
    events.sort(key=lambda e: (e.rec_start_tc, e.parent.track_name))
    return events

##
# Output functions

def output_csv(events, columns, csvfile):
    writer = csv.writer(csvfile)
    
    # Mock output
    writer.writerow(columns)
    
    columns = Config.OUTPUT_COLUMNS
    for e in events:
        row = []
        for col in columns:
            if hasattr(e, col):
                val = getattr(e, col, None)
            else:
                val = e.get_custom(col)
            row.append(val)
        writer.writerow(row)

##
# Main function

def main(inputfile, outputfile=None, **kwargs):
    # output_columns = Config.OUTPUT_COLUMNS
    output_columns = ['Event Number', 'Clip Name' , 'Tape Name',
                      'Link', 'Footage Type',
                      'Footage Source', 'Rec Start',
                      'Rec End', 'Source Start',
                      'Source End']

    events = events_from_xml(inputfile)
    sort_by_tc(events)
    process_events(events)

    with open(outputfile, 'wt', newline='') as csvfile:
        output_csv(events, output_columns, csvfile)

if __name__ == '__main__':
    main(sys.argv[1:])

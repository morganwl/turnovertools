#!/usr/bin/env python3

from itertools import chain
import os
import sys

from turnovertools import xmlobjects

##
# Event processing functions

def remove_filler(e):
    if e.reel is None:
        return None
    return e

def events_from_xml(xmlpath):
    sequence = xmlobjects.XMLSequence.fromfile(xmlpath)[0]
    events = []
    for t in sequence:
        events.extend(t.events)
    return events

def sort_by_tc(events):
    events.sort(key=lambda e: (e.rec_start_tc, e.parent.track_name))
    return events

def main(**kwargs):
    pass

if __name__ == '__main__':
    main()

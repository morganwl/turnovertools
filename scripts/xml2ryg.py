#!/usr/bin/env python3

from itertools import chain
import os
import re
import sys

from turnovertools import xmlobjects

##
# Event processing functions

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

def main(**kwargs):
    pass

if __name__ == '__main__':
    main()

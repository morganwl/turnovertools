#!/usr/bin/env python3

from itertools import chain
import os
import sys

from turnovertools import xmlobjects

def events_from_xml(xmlpath):
    sequence = xmlobjects.XMLSequence.fromfile(xmlpath)[0]
    events = []
    for t in sequence:
        events.extend(t.events)
    return events

def main(**kwargs):
    pass

if __name__ == '__main__':
    main()

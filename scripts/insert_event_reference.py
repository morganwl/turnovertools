#!/usr/bin/env python3

"""Accepts a list of event PrimaryKeys and inserts a reference thumbnail."""

import csv
import os
import sys

from turnovertools import sourcedb
from turnovertools import mediaobjects as mobs

def main(inputfile, table, eventtable):
    if isinstance(eventtable, str):
        eventtable = sourcedb.SourceTable(
            sourcedb.connect(database=eventtable), table=table,
            keyfield='PrimaryKey', mob=mobs.VFXEvent)

    print(eventtable.table, eventtable.keyfield, eventtable._fields)

    with open(inputfile, newline='') as csvfile:
        reader = csv.reader(csvfile)
        events = list(reader)

    mixdowns = dict()

    for key in (row[0] for row in events):
        event = eventtable[key]
        if event is None:
            print(f'No record found for {key}')
            continue
        if event.sequence_name in mixdowns:
            mixdown = mixdowns[event.sequence_name]
        else:
            mixdown = mobs.MediaFile.probe(event.get_custom('video_mixdown'))
            mixdowns[event.sequence_name] = mixdown
        mixdown.mark_start_tc = event.rec_start_tc
        mixdown.mark_end_tc = event.rec_end_tc
        thumbnail = mixdown.thumbnail()
        eventtable.update_container(key, 'image', thumbnail,
                                    f'{event.reel}.jpg')

if __name__ == '__main__':
    main(*sys.argv[1:])

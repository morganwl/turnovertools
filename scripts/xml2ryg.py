#!/usr/bin/env python3

import collections
import csv
from itertools import chain
import os
import re
import sys

import ffmpeg

from turnovertools import xmlobjects, csvobjects

class Config(object):
    OUTPUT_COLUMNS = ['Number', 'clip_name', 'reel', 'Link', 'NOTES',
                      'Footage Type', 'Footage Source', 'rec_start_tc',
                      'rec_end_tc', 'src_start_tc', 'src_end_tc', 'signature']
    FRAME_SIZE = '640x360'
    FRAME_NAMING_CONVENTION = '{:03}_{}.jpg'

##
# Helper functions

def change_ext(filename, ext):
    return os.path.splitext(filename)[0] + ext
    
##
# Event processing functions
def process_events(events):
    new_events = []
    i = 0
    for e in events:
        if e.reel is None:
            continue
        guess_metadata(e)
        e.set_custom('Number', i)
        i += 1
        new_events.append(e)
    return new_events

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
    
    writer.writerow(csvobjects.CSVEvent.convertColumns(columns))
    
    for e in events:
        row = []
        for col in columns:
            if hasattr(e, col):
                val = getattr(e, col, None)
            else:
                val = e.get_custom(col)
            row.append(val)
        writer.writerow(row)

def jpeg_from_pipe(process):
    buffer = []
    dangling_code = False # in case an end code straddles two chunks
    chunk = process.stdout.read()
    
    # keep reading chunks off of stdout until the process terminates
    while len(chunk) or process.poll() is None:
        while len(chunk):
            # look for an end-of-image code
            if dangling_code and chunk[0] == b'\xd9':
                end_code = 1
            else:
                end_code = chunk.find(b'\xff\xd9') + 2

            # if we found an end_code, flush the buffer as an image
            if end_code > 1:
                buffer.append(chunk[:end_code])
                yield(b''.join(buffer))

                buffer = []
                chunk = chunk[end_code:]
                if len(chunk) > 2 and chunk.find(b'\xff\xd8\xff') != 0:
                    raise Exception('Unexpected byte-string', chunk[0:3])
            else:
                if len(chunk) and chunk[-1] == b'x\ff':
                    dangling_code = True
                else:
                    dangling_code = False
                buffer.append(chunk)
        chunk = process.stdout.read()
    

def output_frames(events, videofile, outdir):
    # create a dictionary of frames, where each key corresponds to a
    # frame number in videofile, and contains a list of events for
    # that frame. (Some stacked events will use the same poster frame)
    frame_numbers = collections.defaultdict(list)
    for e in events[0:4]:
        frame = int(e.rec_start_frame) + e.posterframes[0]
        frame_numbers[frame].append(e)
    framestrings = []
    for frame in frame_numbers:
        framestrings.append("eq(n,{})".format(frame))
    ffmpeg_command = (
        ffmpeg
        .input(videofile)
        .filter('select', '+'.join(framestrings))
        .filter('scale', Config.FRAME_SIZE)
        .output('pipe:', format='image2pipe', vcodec='mjpeg', q=1, vsync=0)
    )
    
    process = ffmpeg.run_async(ffmpeg_command, pipe_stdout=True,
                               pipe_stderr=True)

    for img, frames in zip(jpeg_from_pipe(process), frame_numbers.values()):
        for e in frames:
            img_name = Config.FRAME_NAMING_CONVENTION.\
                format(e.get_custom('Number'), e.clip_name)
            with open(os.path.join(outdir, img_name), 'wb') as img_file:
                img_file.write(img)
                print('{} bytes written to {}'.format(len(img), img_name))

    process.communicate()


##
# Main function

def main(inputfile, outputfile=None, videofile=None,
         frameoutput=None, **kwargs):
    output_columns = Config.OUTPUT_COLUMNS

    events = events_from_xml(inputfile)
    sort_by_tc(events)
    events = process_events(events)

    if outputfile is None:
        outputfile = change_ext(inputfile, '.csv')
    with open(outputfile, 'wt', newline='') as csvfile:
        output_csv(events, output_columns, csvfile)

    if videofile:
        output_frames(events, videofile, frameoutput)

if __name__ == '__main__':
    main(sys.argv[1:])

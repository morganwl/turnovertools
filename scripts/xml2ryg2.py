#!/usr/bin/env python3

import argparse
import collections
import csv
from itertools import chain
import os
import re
import sys

import edl
import ffmpeg

from turnovertools.edlobjects import EDLEvent
from turnovertools import linkfinder, csvobjects

class Config(object):
    OUTPUT_COLUMNS = ['Number', 'clip_name', 'reel', 'Link', 'NOTES',
                      'Footage Type', 'Footage Source', 'rec_start_tc',
                      'rec_end_tc', 'src_start_tc', 'src_end_tc', 'signature']
    FRAME_SIZE = '640x360'
    FRAME_NAMING_CONVENTION = '{:03}_{}.jpg'
    VIDEO_NAMING_CONVENTION = '{:03}_{}.mp4'
    VIDEO_SCALE = '960x540'
    MATCHERS = [ linkfinder.GettyMatcher(), linkfinder.ShutterMatcher() ]

def change_ext(filename, ext):
    return os.path.splitext(filename)[0] + ext

def events_from_edl(inputfile):
    parser = edl.Parser('23.98')
    with open(inputfile) as fh:
        edit_list = parser.parse(fh)
    seq_start = edit_list.get_start()
    events = list()
    for e in edit_list.events:
        events.append(EDLEvent(seq_start, e))
    return events

def process_events(events, ale_file=None):
    matchers = Config.MATCHERS
    matchers.insert(0, linkfinder.ALEMatcher('/Users/wajdalevie/private_test_files/turnover_tools/LG_R1_200303_RYG.ALE'))
    i = 0
    for e in events:
        e.link = linkfinder.process(e.reel, matchers)
        e.number = i
        i += 1

def output_csv(events, columns, csvfile):
    writer = csv.writer(csvfile)
    
    writer.writerow(csvobjects.CSVEvent.convertColumns(columns))
    
    for e in events:
        row = []
        for col in columns:
            if hasattr(e, col.lower()):
                val = getattr(e, col.lower(), None)
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
    for e in events:
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

def output_video(events, videofile, outdir):
    #TO-DO: add support for varying framerates
    for e in events:
        rec_start_seconds = int(e.rec_start_frame) / 23.976
        rec_duration_seconds = (int(e.rec_end_frame) - 
                                int(e.rec_start_frame) + 1) / 23.976
        video_name = Config.VIDEO_NAMING_CONVENTION.format(
            e.get_custom('Number'), e.clip_name)
        command = (
            ffmpeg
            .input(videofile, ss=rec_start_seconds)
            .filter('scale', Config.VIDEO_SCALE)
            .output(
                os.path.join(outdir, video_name),
                vcodec='h264', pix_fmt='yuv420p',
                t=rec_duration_seconds)
            )
        ffmpeg.run(command, capture_stdout=True, capture_stderr=True)
        print('Video written to {}'.format(video_name))

def parse_arguments(args):
    parser = argparse.ArgumentParser(prog=args[0])
    parser.add_argument('input')
    parser.add_argument('outputfile', nargs='?', default=None)
    parser.add_argument('-v', '--videofile')
    parser.add_argument('-fo', '--frame-output', dest='frameoutput')
    parser.add_argument('-vo', '--video-output', dest='videooutput')
    return parser.parse_args(args[1:])

def main(inputfile, outputfile=None, videofile=None,
         frameoutput=None, videooutput=None, **kwargs):
    output_columns = Config.OUTPUT_COLUMNS
    
    events = events_from_edl(inputfile)
    #sort_by_tc(events)
    process_events(events)

    if outputfile is None:
        outputfile = change_ext(inputfile, '.csv')
    with open(outputfile, 'wt', newline='') as csvfile:
        output_csv(events, output_columns, csvfile)

    if videofile and frameoutput:
        output_frames(events, videofile, frameoutput)

    if videofile and videooutput:
        output_video(events, videofile, videooutput)

def xml2ryg2():
    args = parse_arguments(sys.argv)
    main(args.input, **(vars(args)))

if __name__ == '__main__':
    xml2ryg2()

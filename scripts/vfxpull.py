#!/usr/bin/env python3

import csv
import os
import sys

import edl
from timecode import Timecode

from turnovertools.edlobjects import EDLEvent
from turnovertools import csvobjects

class Config(object):
    DEFAULT_HANDLES = 8
    ALE_TRANSLATE = { 'clip_name' : 'Name', 'reel': 'Tape',
    'src_start_tc' : 'Start', 'src_end_tc' : 'End', 'tracks' :
    'Tracks', 'frame_count_start' : 'Frame Count Start'}

def read_csv(inputfile):
    rows = list()
    with open(inputfile, newline='') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows

def add_handles(subclip, handles=None):
    if handles is None:
        handles = Config.DEFAULT_HANDLES
    start_tc = Timecode(24, subclip['src_start_tc']) - handles
    end_tc = Timecode(24, subclip['src_end_tc']) + handles
    subclip['src_start_tc'] = str(start_tc)
    subclip['src_end_tc'] = str(end_tc)
    subclip['frame_count_start'] = '1001'

def vfx_id_element(clip):
    s = clip['vfx_id']
    if clip['vfx_element']:
        s += '_' + clip['vfx_element']
    return s

def write_ale(filename, clips):
    columns = [ 'clip_name', 'reel', 'src_start_tc', 'src_end_tc',
                'frame_count_start', 'tracks']
    with open(filename, 'w') as fh:
        write_ale_header(fh)
        write_ale_columns(fh, columns)
        write_ale_data(fh, columns, clips)

def write_ale_header(fh):
    fh.write('Heading\n')
    fh.write('FIELD_DELIM\tTABS\n')
    fh.write('VIDEO_FORMAT\t1080\n')
    fh.write('AUDIO_FORMAT\t48khz\n')
    fh.write('FPS\t23.976\n\n')

def write_ale_columns(fh, columns):
    fh.write('Column\n')
    for col in columns:
        fh.write(Config.ALE_TRANSLATE[col]+'\t')
    fh.write('\n')

def write_ale_data(fh, columns, clips):
    fh.write('Data\n')
    for clip in clips:
        if not clip['vfx_id']:
            continue
        for col in columns:
            fh.write(clip[col]+'\t')
        fh.write('\n')

def main(inputfile):
    # read in csv
    subclips = read_csv(inputfile)

    # assume all elements are for pull
    # for now, add blanket handles. will need to re-assess later.
    for sc in subclips:
        add_handles(sc)
        sc['clip_name'] = vfx_id_element(sc)
        sc['tracks'] = 'V'

    # export ale
    write_ale('out.ale', subclips)

    # create EDL sequence

    # string clips out, no speed effect

    # export EDL
    

if __name__ == '__main__':
    main(sys.argv[1])

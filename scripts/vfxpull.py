#!/usr/bin/env python3

from collections import defaultdict
import csv
import os
import sys

import edl
from timecode import Timecode

from turnovertools.edlobjects import EDLEvent
from turnovertools import csvobjects, interface
from turnovertools.config import Config

# TO-DO: real ALE support
Config.ALE_TRANSLATE = { 'clip_name' : 'Name',
                         'reel': 'Tape',
                         'src_start_tc' : 'Start',
                         'src_end_tc' : 'End',
                         'tracks' : 'Tracks',
                         'frame_count_start' : 'Frame Count Start'}

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

def write_ale(filename, fr_groups):
    columns = [ 'clip_name', 'reel', 'src_start_tc', 'src_end_tc',
                'frame_count_start', 'tracks']
    for fr, subclips in fr_groups.items():
        fn = filename.replace('.ale', f'_{fr}.ale')
        with open(fn, 'w') as fh:
            write_ale_header(fh)
            write_ale_columns(fh, columns)
            write_ale_data(fh, columns, subclips)

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

def write_edl(output_base, fr_groups):
    for fr, subclips in fr_groups.items():
        title = f'{output_base}_{fr}'
        pull_list = build_edl(fr, subclips, title)

        # TO-DO: need to write our own much stronger EDL output
        # methods, as the python-edl ones do not work
        with open(f'{title}.edl', 'wt') as fh:
            fh.write(f'TITLE:   {pull_list.title} \n')
            fh.write(f'FCM: {pull_list.fcm}\n')
            for e in pull_list:
                fh.write(f'{e.num}  {e.reel:32} {e.tr_code:6}{e.aux:9}')
                fh.write(f'{e.src_start_tc} {e.src_end_tc} {e.rec_start_tc} {e.rec_end_tc} \n')
                if(e.clip_name):
                    fh.write(f'*FROM CLIP NAME:  {e.clip_name} \n')

def build_edl(fr, subclips, title=''):
    pull_list = edl.List(Config.DEFAULT_FRAMERATE)
    pull_list.title = title
    pull_list.fcm = 'NON-DROP FRAME'
    next_tc = Timecode(fr, '01:00:00:00')
    for num, sc in enumerate(subclips, 1):
        # TO-DO: Rewrite Event __init__ method in python-edl

        # python-edl Event __init__ expects a dictionary, not a list
        # of keywords, so building that dictionary this way to make it
        # easier to switch back to keywords if I get around to
        # updating the python-edl library
        src_start_tc = Timecode(fr, sc['src_start_tc'])
        src_end_tc = Timecode(fr, sc['src_end_tc'])
        options = dict(reel=sc['reel'],
                       clip_name=sc['vfx_id'],
                       src_start_tc=src_start_tc,
                       src_end_tc=src_end_tc,
                       rec_start_tc=next_tc,
                       rec_end_tc=next_tc + src_end_tc - src_start_tc,
                       tr_code='V',
                       aux='C',
                       num=f'{num:06d}')
        e = edl.Event(options)
        pull_list.append(e)
        next_tc = pull_list[-1].rec_end_tc

    return pull_list

def group_by_framerate(subclips):
    """Receives a list of subclips and returns a dictionary of lists, with
    lists keyed to framerate."""
    subclips_by_framerate = defaultdict(list)
    for sc in subclips:
        subclips_by_framerate[sc['src_framerate']].append(sc)
    return subclips_by_framerate

def main(inputfile, outputdir=None, **kwargs):
    input = interface.Input(inputfile, outputdir=outputdir)

    # read in csv
    subclips = read_csv(inputfile)

    # assume all elements are for pull
    # for now, add blanket handles. will need to re-assess later.
    for sc in subclips:
        add_handles(sc)
        sc['clip_name'] = vfx_id_element(sc)
        sc['tracks'] = 'V'

    # group subclips by group framerate (list of lists)
    fr_groups = group_by_framerate(subclips)
        
    # export ale
    write_ale(input.output_ale, fr_groups)

    # create EDL sequence
    write_edl(input.output_base, fr_groups)

    print(input.outputdir)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

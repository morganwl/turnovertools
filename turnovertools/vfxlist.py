import csv
import os
import sys

import edl
from timecode import Timecode

def read_csv(inputfile):
    rows = list()
    with open(inputfile, newline='') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows

def read_vfx_csv(inputfile):
    vfxlist = list()
    for clip in read_csv(inputfile):
        if clip['vfx_id']:
            vfxlist.append(clip)
    return vfxlist

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

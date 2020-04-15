"""Functions for reading vfx lists."""

import csv
from timecode import Timecode

from turnovertools import Config
from turnovertools import mediaobjects as mobs

def read_csv(filehandle):
    """Reads a csv from a file-like object and yields a dict for each
    row."""
    reader = csv.DictReader(filehandle)
    for row in reader:
        yield row

def read_vfx_csv(filehandle):
    """Parses a csv from a file-like object and returns a list of
    mobs.VFXEvent objects."""
    vfxlist = list()
    for clip in read_csv(filehandle):
        if clip['vfx_id']:
            remove_empty = {key: value for key, value in clip.items() if value}
            vfxlist.append(mobs.VFXEvent(**remove_empty))
    return vfxlist

def add_handles(subclip, handles=None):
    """Adds Config.DEFAULT_HANDLES number of handles to src_tc of a
    vfx dict."""
    if handles is None:
        handles = Config.DEFAULT_HANDLES
    start_tc = Timecode(24, subclip['src_start_tc']) - handles
    end_tc = Timecode(24, subclip['src_end_tc']) + handles
    subclip['src_start_tc'] = str(start_tc)
    subclip['src_end_tc'] = str(end_tc)
    subclip['frame_count_start'] = '1001'

def vfx_id_element(clip):
    """Returns the vfx_id with an element suffix, if present, from a
    vfx dict."""
    s = clip['vfx_id']
    if clip['vfx_element']:
        s += '_' + clip['vfx_element']
    return s

#!/usr/bin/env python3

"""
vfxpull.py

Usage: vfxpull.py input.csv [outputdir]
Reads a vfx list as a csv, applies handles (either specified in
scan_start_tc, etc or using default values set in
config.Config.DEFAULT_HANDLES) and outputs a pull EDL and a pull ALE.
"""

from collections import defaultdict
import os
import warnings
import sys

import edl

from turnovertools import interface
from turnovertools.config import Config
from turnovertools.vfxlist import read_vfx_csv
from turnovertools.mediaobjects import Timecode

# TO-DO: real ALE support
Config.ALE_TRANSLATE = {'clip_name' : 'Name',
                        'reel': 'Tape',
                        'src_start_tc' : 'Start',
                        'src_end_tc' : 'End',
                        'tracks' : 'Tracks',
                        'frame_count_start' : 'Frame Count Start'}

def add_handles(subclip, handles=None):
    """If scan timecodes are specified, sets the src_start_tc,
    src_end_tc and frame_count_start to match. Otherwise, adds handles
    according to Config.DEFAULT_HANDLES."""
    if handles is None:
        handles = Config.DEFAULT_HANDLES
    if isinstance(subclip, dict):
        warnings.warn('Dictionary usage is deprecated. Please pass an ' +
                      'appropriate Mob instead.', DeprecationWarning)
        _add_handles_dict(subclip, handles)
        return
    if subclip.scan_start_tc is None:
        subclip.src_start_tc -= handles
    else:
        subclip.src_start_tc = subclip.scan_end_tc
    if subclip.scan_end_tc is None:
        subclip.src_end_tc += handles
    else:
        subclip.src_end_tc = subclip.scan_end_tc
    if subclip.scan_count_start is None:
        subclip.frame_count_start -= handles
    else:
        subclip.frame_count_start = subclip.scan_count_start

def _add_handles_dict(subclip, handles=None):
    """Deprecated version of add_handles that operates on a dictionary
    instead of a Mobs object."""
    start_tc = Timecode(24, subclip['src_start_tc']) - handles
    end_tc = Timecode(24, subclip['src_end_tc']) + handles
    subclip['src_start_tc'] = str(start_tc)
    subclip['src_end_tc'] = str(end_tc)
    subclip['frame_count_start'] = '1001'

def vfx_id_element(vfxevent):
    if isinstance(vfxevent, dict):
        warnings.warn('Dictionary usage is deprecated. Please pass an appropriate Mob instead.', DeprecationWarning)
        return _vfx_id_element_dict(vfxevent)
    return vfxevent.vfx_id_element

def _vfx_id_element_dict(clip):
    buffer = list()
    buffer.append(clip['vfx_id'])
    buffer.append(clip['vfx_element'])
    return '_'.join(filter(None, buffer))

def vfxlist_to_ale(vfxlist, framerate):
    """Accepts a list of mobs and their framerate and outputs an ALE as a
    string."""
    columns = ['clip_name', 'reel', 'src_start_tc', 'src_end_tc',
               'frame_count_start', 'tracks']
    buffer = list()

    # header
    buffer.extend(('Heading', 'FIELD_DELIM\tTABS', 'VIDEO_FORMAT\t1080',
                   'AUDIO_FORMAT\t48khz', f'FPS\t{str(framerate)}', ''))

    # column header
    buffer.append('Column')
    tab_buffer = list()
    for col in columns:
        tab_buffer.append(Config.ALE_TRANSLATE[col])
    buffer.append('\t'.join(tab_buffer))

    # clip data
    buffer.append('Data')
    for clip in vfxlist:
        tab_buffer = list()
        for col in columns:
            tab_buffer.append(str(getattr(clip, col, '')))
        buffer.append('\t'.join(tab_buffer))
    return '\n'.join(buffer)


def write_ale(output_base, fr_groups):
    columns = ['clip_name', 'reel', 'src_start_tc', 'src_end_tc',
               'frame_count_start', 'tracks']
    for framerate, subclips in fr_groups.items():
        filename = f'{output_base}_{framerate}.ale'
        with open(filename, 'w') as filehandle:
            write_ale_header(filehandle)
            write_ale_columns(filehandle, columns)
            write_ale_data(filehandle, columns, subclips)

def write_ale_header(filehandle):
    filehandle.write('Heading\n')
    filehandle.write('FIELD_DELIM\tTABS\n')
    filehandle.write('VIDEO_FORMAT\t1080\n')
    filehandle.write('AUDIO_FORMAT\t48khz\n')
    filehandle.write('FPS\t23.976\n\n')

def write_ale_columns(filehandle, columns):
    filehandle.write('Column\n')
    for col in columns:
        filehandle.write(Config.ALE_TRANSLATE[col]+'\t')
    filehandle.write('\n')

def write_ale_data(filehandle, columns, clips):
    filehandle.write('Data\n')
    for clip in clips:
        if not clip['vfx_id']:
            continue
        for col in columns:
            filehandle.write(clip[col]+'\t')
        filehandle.write('\n')

def _write_edl_dict(output_base, fr_groups):
    for framerate, subclips in fr_groups.items():
        title = f'{output_base}_{framerate}'
        pull_list = _build_edl_dict(framerate, subclips, title)

        # TO-DO: need to write our own much stronger EDL output
        # methods, as the python-edl ones do not work
        with open(f'{title}.edl', 'wt') as filehandle:
            filehandle.write(f'TITLE:   {pull_list.title} \n')
            filehandle.write(f'FCM: {pull_list.fcm}\n')
            for event in pull_list:
                filehandle.write(f'{event.num}  {event.reel:32} {event.tr_code:6}{event.aux:9}')
                filehandle.write(f'{event.src_start_tc} {event.src_end_tc} {event.rec_start_tc} {event.rec_end_tc} \n')
                if event.clip_name:
                    filehandle.write(f'*FROM CLIP NAME:  {event.clip_name} \n')

def clip_stringout(clips, start_timecode=None):
    if start_timecode is None:
        start_timecode = Timecode(Config.DEFAULT_FRAMERATE, '01:00:00:00')
    next_tc = start_timecode
    stringout = list()
    for clip in clips:
        clip.rec_start_tc = next_tc
        next_tc += clip.src_duration
        clip.rec_end_tc = next_tc    # end TC is exclusive
        stringout.append(clip)
    return stringout

def stringout_to_edl(stringout, framerate, title=''):
    edit_list = edl.List(framerate)
    edit_list.title = title
    edit_list.fcm = 'NON-DROP FRAME'
    for num, event in enumerate(stringout, 1):
        options = dict(reel=event.reel,
                       clip_name=event.clip_name,
                       src_start_tc=event.src_start_tc,
                       src_end_tc=event.src_end_tc,
                       rec_start_tc=event.rec_start_tc,
                       rec_end_tc=event.rec_end_tc,
                       tr_code='V',
                       aux='C',
                       num=f'{num:06d}')
        edit_list.append(edl.Event(options))
    return edit_list

def edl_to_str(edit_list):
    buffer = list()

    #header
    buffer.append(f'TITLE:   {edit_list.title}')
    buffer.append(f'FCM: {edit_list.fcm}')

    #body
    for event in edit_list:
        event_buffer = list()
        event_buffer.append(f'{event.num:7}')
        event_buffer.append(f'{event.reel:32}')
        event_buffer.append(f'{event.tr_code:5}')
        event_buffer.append(f'{event.aux:8}')
        event_buffer.append(str(event.src_start_tc))
        event_buffer.append(str(event.src_end_tc))
        event_buffer.append(str(event.rec_start_tc))
        event_buffer.append(str(event.rec_end_tc))
        buffer.append(' '.join(event_buffer))
        if event.clip_name:
            buffer.append(f'*FROM CLIP NAME:  {event.clip_name}')
    return '\n'.join(buffer)


def _build_edl_dict(framerate, subclips, title=''):
    pull_list = edl.List(Config.DEFAULT_FRAMERATE)
    pull_list.title = title
    pull_list.fcm = 'NON-DROP FRAME'
    next_tc = Timecode(framerate, '01:00:00:00')
    for num, subclip in enumerate(subclips, 1):
        # TO-DO: Rewrite Event __init__ method in python-edl

        # python-edl Event __init__ expects a dictionary, not a list
        # of keywords, so building that dictionary this way to make it
        # easier to switch back to keywords if I get around to
        # updating the python-edl library
        src_start_tc = Timecode(framerate, subclip['src_start_tc'])
        src_end_tc = Timecode(framerate, subclip['src_end_tc'])
        options = dict(reel=subclip['reel'],
                       clip_name=subclip['vfx_id'],
                       src_start_tc=src_start_tc,
                       src_end_tc=src_end_tc,
                       rec_start_tc=next_tc,
                       rec_end_tc=next_tc + src_end_tc - src_start_tc,
                       tr_code='V',
                       aux='C',
                       num=f'{num:06d}')
        event = edl.Event(options)
        next_tc = event.rec_end_tc
        pull_list.append(event)

    return pull_list

def group_by_framerate(subclips):
    """Receives a list of subclips and returns a dictionary of lists, with
    lists keyed to framerate."""
    subclips_by_framerate = defaultdict(list)
    for subclip in subclips:
        if isinstance(subclip, dict):
            warnings.warn('Dictionary usage is deprecated. Please pass an appropriate Mob instead.', DeprecationWarning)
            subclips_by_framerate[subclip['src_framerate']].append(subclip)
            continue
        subclips_by_framerate[subclip.src_framerate].append(subclip)
    return subclips_by_framerate

def vfxlist_to_edl(vfxlist, framerate, title):
    stringout = clip_stringout(vfxlist, Timecode(framerate, '01:00:00:00'))
    edit_list = stringout_to_edl(stringout, framerate, title)
    return edl_to_str(edit_list)

def process_input(filehandle):
    subclips = read_vfx_csv(filehandle)
    for subclip in subclips:
        add_handles(subclip)
        subclip.clip_name = subclip.vfx_id_element
        subclip.tracks = 'V'
    return subclips

def main(inputfile, outputdir=None):
    user_input = interface.UserInput(inputfile, outputdir=outputdir)

    # read in csv
    with open(inputfile) as filehandle:
        subclips = process_input(filehandle)

    # group subclips by group framerate (list of lists)
    fr_groups = group_by_framerate(subclips)

    for framerate, vfxlist in fr_groups.items():
        title = f'{user_input.output_base}_{framerate.replace(".", "")}'
        ale_file = os.path.join(user_input.outputdir, f'{title}.ale')
        with open(ale_file, 'wt') as ale_output:
            ale_output.write(vfxlist_to_ale(vfxlist, framerate))
        edl_file = os.path.join(user_input.outputdir, f'{title}.edl')
        with open(edl_file, 'wt') as edl_output:
            edl_output.write(vfxlist_to_edl(vfxlist, framerate, title))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

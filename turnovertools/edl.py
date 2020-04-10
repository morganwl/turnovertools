import os

import edl
from timecode import Timecode

from turnovertools.edlobjects import EDLEvent

##########
# Patches for python-edl bug with mixed framerates
##########

def detruncate_timecode(tc, new_framerate):
    new_tc = Timecode(new_framerate, str(tc - tc.frs - 1)) + tc.frs + 1
    return new_tc

def flag_mixed_rate(evt, line):
    evt._src_start_tc_overflow = False
    evt._src_end_tc_overflow = False
    if str(evt.src_start_tc) not in line:
        evt._src_start_tc_overflow = True
    if str(evt.src_end_tc) not in line:
        evt._src_end_tc_overflow = True

def apply_timewarp_fps(evt):
    for c in evt.comments:
        if c.startswith('*TIMEWARP EFFECT'):
            return    
    if evt._src_start_tc_overflow:
        evt.src_start_tc = detruncate_timecode(evt.src_start_tc,
                                               evt.timewarp.warp_fps)
    if evt._src_end_tc_overflow:
        evt.src_end_tc = detruncate_timecode(evt.src_end_tc,
                                             evt.timewarp.warp_fps)

# fix a bug in python-edl with mixed-rate timecodes
def fix_mixed_rate(evt):
    if evt.has_timewarp():
        apply_timewarp_fps(evt)
    del evt._src_start_tc_overflow
    del evt._src_end_tc_overflow
    evt.src_framerate = evt.src_start_tc.framerate

event_old_apply = edl.EventMatcher.apply
def event_patched_apply(self, stack, line):
    evt = event_old_apply(self, stack, line)
    if evt:
        flag_mixed_rate(evt, line)
        if len(stack) > 1:
            fix_mixed_rate(stack[-2])
    return evt
edl.EventMatcher.apply = event_patched_apply

parser_old_parse = edl.Parser.parse
def parser_patched_parse(self, input_):
    stack = parser_old_parse(self, input_)
    fix_mixed_rate(stack[-1])
    return stack
edl.Parser.parse = parser_patched_parse

##########
##########

def change_ext(filename, ext):
    return os.path.splitext(filename)[0] + ext

def events_from_edl(edl_files):
    tmp_events = list()
    seq_start = Timecode('23.98', '23:59:59:23')
    edit_lists = list()
    for file in edl_files:
        edit_list = import_edl(file)
        edit_list.filename = os.path.basename(file)
        if edit_list.get_start().frames < seq_start.frames:
            seq_start = edit_list.get_start()
        edit_lists.append(edit_list)
    events = list()
    for l in edit_lists:
        for e in l:
            if e.has_transition():
                # to the best I can tell, the event before
                # has_transition is a dummy event
                del events[-1]
                add_transition_out(events[-1], e)
                add_transition_in(e, e.next_event)
                continue
            events.append(EDLEvent(seq_start, e))
            e.sequence_name = l.title
            e.track = fn_to_track(l.filename)
    return events

def add_transition_out(e, tr):
    if e is None or e.rec_end_tc != tr.rec_start_tc:
        # skip instances where the prior event does not exist or does
        # not precede the transition (like if transition is first
        # event in a track)
        return
    e.src_end_tc += int(e.speed * tr.incoming_transition_duration())
    e.rec_end_tc = tr.rec_end_tc

def add_transition_in(tr, e):
    if e is None or tr.rec_end_tc != e.rec_start_tc:
        return
    speed = e.src_length() / e.rec_length()
    e.src_start_tc -= int(speed * tr.incoming_transition_duration())
    e.rec_start_tc = tr.rec_start_tc

def get_src_end_with_transition(e, tr_end_tc):
    fade_duration = e

def fn_to_track(fn):
    return change_ext(fn, '').rsplit('_', 1)[1].replace('V', '')

def import_edl(edl_file):
    parser = edl.Parser('23.98')
    with open(edl_file) as fh:
        edit_list = parser.parse(fh)
    return edit_list

#!/usr/bin/env python3

from abc import ABCMeta

import edl
from timecode import Timecode

from . import mediaobject


class EDLWrapper(ABCMeta):
    def __new__(meta, name, bases, class_dict):
        lookup = class_dict.get('__lookup__', {})
        for prop, target in lookup.items():
            if prop not in class_dict:
                class_dict[prop] = property(meta.getmapper(target),
                                            meta.setmapper(target))
        cls = type.__new__(meta, name, bases, class_dict)
        return cls

    def getmapper(target):
        def getter(self):
            return getattr(self.data, target, None)
        return getter

    def setmapper(lookup):
        def setter(self, val):
            setattr(self.data, lookup, val)
        return setter


class EDLObject(object, metaclass=EDLWrapper):
    pass

class EDLEvent(mediaobject.Event, EDLObject):
    __lookup__ = {'clip_name' : 'clip_name',
                  'tape_name' : 'tape_name',
                  'source_file' : 'source_file',
                  'src_start_tc' : 'src_start_tc',
                  'src_end_tc' : 'src_end_tc',
                  'rec_start_tc' : 'rec_start_tc',
                  'rec_end_tc' : 'rec_end_tc',
                  'event_num' : 'num',
                  'track' : 'track',
                  'asc_sop': 'asc_sop',
                  'asc_sat': 'asc_sat'}
    __wraps_type__ = edl.Event

    def __init__(self, seq_start, data=None, **kwargs):
        super(EDLEvent, self).__init__(data=data, **kwargs)
        self._seq_start = seq_start

    def get_custom(self, name):
        return getattr(self.data, name.lower(), None)

    def set_custom(self, name, val):
        setattr(self.data, name.lower(), val)

    @property
    def rec_start_frame(self):
        return (self.rec_start_tc - self._seq_start).frames

    @property
    def rec_end_frame(self):
        return self.rec_start_frame + self.data.rec_length() - 1

    @property
    def speed(self):
        return self.data.src_length() / self.data.rec_length()

    @property
    def comments(self):
        return self.data.comments

    @property
    def locators(self):
        locators = list()
        for c in self.comments:
            if c.startswith('* LOC:'):
                locators.append(c)
        return locators

    @property
    def asc_sop(self):
        for c in self.comments:
            if c.startswith('* ASC_SOP'):
                return c[c.find('('):]

    @property
    def asc_sat(self):
        for c in self.comments:
            if c.startswith('* ASC_SAT'):
                return c.split('ASC_SAT ', 1)[1]

    def src_tc_at(self, rec_tc):
        offset = Timecode(self.rec_start_tc.framerate, rec_tc) - self.rec_start_tc
        return self.src_start_tc + int(offset.frames * self.speed)

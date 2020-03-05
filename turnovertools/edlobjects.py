#!/usr/bin/env python3

from abc import ABCMeta

from . import mediaobject

class EDLWrapperMeta(ABCMeta):
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
            setattr(self.data, target, val)
        return setter

class EDLObject(metaclass=EDLWrapperMeta):
    pass

class EDLEvent(mediaobject.Event, EDLObject):
    __lookup__ = {'clip_name' : 'Clip Name',
                  'tape_name' : 'tape_name',
                  'source_file' : 'source_file',
                  'src_start_tc' : 'src_start_tc',
                  'src_end_tc' : 'src_end_tc',
                  'rec_start_tc' : 'rec_start_tc',
                  'rec_end_tc' : 'rec_end_tc',
                  'event_num' : 'num'}

    wraps_type = edl.Event

    def __init__(self, seq_start, data=None, **kwargs):
        super(EDLEvent, self).__init__(data=data, **kwargs)
        self._abs_rec_start = self.rec_start_tc - seq_start

    def get_custom(self, name):
        return getattr(self.data, name, None)

    def set_custom(self, name, val):
        setattr(self.data, name, val)

    @property
    def rec_start_frame(self):
        return self._abs_rec_start.frames
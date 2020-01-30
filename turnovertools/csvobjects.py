from abc import ABCMeta
import collections

from . import mediaobject

class DictWrapperMeta(ABCMeta):
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
            return self.data.get(target, None)
        return getter

    def setmapper(lookup):
        def setter(self, val):
            self.data[target] = val
        return setter

class CSVObject(metaclass=DictWrapperMeta):
    pass

class CSVEvent(mediaobject.Event, CSVObject):
    __lookup__ = {'clip_name' : 'Clip Name',
                  'reel' : 'Tape Name',
                  'tape_name' : 'Tape Name',
                  'source_file' : 'Source File',
                  'src_start_tc' : 'Source Start',
                  'src_end_tc' : 'Source End',
                  'rec_start_tc' : 'Rec Start',
                  'rec_end_tc' : 'Rec End',
                  'src_start_frame' : 'Source Start Frame',
                  'src_end_frame' : 'Source End Frame',
                  'rec_start_frame' : 'Rec Start Frame',
                  'rec_end_frame' : 'Rec End Frame',
                  'event_num' : 'Event Number',
                  'link' : 'Link'}

    wraps_type = collections.OrderedDict

    def get_custom(self, name):
        return self.data.get(name, None)

    def set_custom(self, name, val):
        self.data[name] = val

    @classmethod
    def convertColumns(cls, columns):
        newColumns = []
        for col in columns:
            newColumns.append(cls.__lookup__.get(col, col))
        return newColumns

#!/usr/bin/env python3

from abc import ABCMeta
import collections.abc

class MediaObject(object):
    """
    Parent class for all media objects. Not meant to be instantiated directly.
    """
    __wraps_type__ = type(None)
    __default_data__ = []
    __requires_properties__ = []

    @classmethod
    def wrap_list(cls, data_list, parent=None, **kwargs):
        """
        Wraps a list of data objects using the given MediaObject child
        class, returning them in a new list.
        """
        mob_list = []
        for d in data_list:
            mob_list.append(cls(d, parent=parent, **kwargs))
        return mob_list

    def __init__(self, data=None, parent=None, **kwargs):
        """
        Instantiate MediaObject with a new data object, or with
        kwargs.
        """
        self.parent = parent
        if data is not None:
            assert isinstance(data, self.__wraps_type__)
            self.data = data
        else:
            self.data = self.__wraps_type__(*self.default_data)
        for key, val in kwargs.items():
            if key in self.__requires_properties__:
                setattr(self, key, val)
            else:
                raise AttributeError('Invalid keyword parameter ' + key)

    def __setattr__(self, key, value):
        """
        Optionally call a private _on_update method whenever
        attributes are changed in this object.
        """
        self._on_update(key, value)
        super(MediaObject, self).__setattr__(key, value)

    def _on_update(self, key, value):
        pass

class Sequence(MediaObject, collections.abc.Sequence):
    def __init__(self, data=None, **kwargs):
        super(Sequence, self).__init__(data=data, **kwargs)
        self.tracks = []

    def __getitem__(self, i):
        return self.tracks[i]

    def __len__(self):
        return len(self.tracks)

class SequenceTrack(MediaObject, collections.abc.Sequence):
    def __init__(self, data=None, **kwargs):
        super(SequenceTrack, self).__init__(data=data, **kwargs)
        self.events = []

    def __getitem__(self, i):
        return self.events[i]

    def __len__(self):
        return len(self.events)

class Event(MediaObject):
    __requires_properties__ = ['clip_name']

    def get_custom(self, name):
        raise NotImplementedError()

    @property
    def posterframes(self):
        """Returns a list of posterframes (in record), or rec_start_frame in
        list form."""
        if getattr(self, '_posterframes', None):
            return self._posterfames
        return [0]

    @posterframes.setter
    def posterframes(self, val):
        self._posterframes = val;

    @property
    def reel(self):
        if self.tape_name is not None:
            return self.tape_name
        return self.source_file

    @reel.setter
    def reel(self, val):
        if self.source_file is not None:
            self.source_file = val
        self.tape_name = val

class SourceClip(MediaObject):
    def get_custom(self, name):
        raise NotImplementedError()

    @property
    def reel(self):
        if self.tape_name is not None:
            return self.tape_name
        return self.source_file

    @reel.setter
    def reel(self, val):
        if self.source_file is not None:
            self.source_file = val
        self.tape_name = val
    

class Bin(MediaObject):
    pass

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

class DictWrapper(object, metaclass=DictWrapperMeta):
    __wraps_type__ = dict

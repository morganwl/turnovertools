#!/usr/bin/env python3

import xmlparser

import mediaobject

class XMLWrapper(type):
    def __new__(meta, name, bases, class_dict):
        lookup = class_dict.get('__lookup__', {})
        for prop, target in lookup.items():
            if prop not in class_dict:
                class_dict[prop] = property(meta.getmapper(*target),
                                            meta.setmapper(*target))
        cls = type.__new__(meta, name, bases, class_dict)
        return cls

    def getmapper(path, attrib=None, attr='text'):
        def getter(self):
            targets = self.data.findall(path)
            if len(targets) == 0:
                return None
            if len(targets) > 1:
                raise Exception('Found multiple elements for ' + path)
            if attrib is None:
                return getattr(targets[0], attr, None)
            else:
                return targets[0].attrib.get(attrib, None)
        return getter

    def setmapper(path, attrib=None, attr='text'):
        def setter(self, val):
            found = self.data.findall(path)
            if len(found) == 0:
                pass
            if len(found) == 1:
                if attrib is None:
                    found[0][attr] = val
                else:
                    found[0].attrib[attrib] = val
        return setter

class XMLEvent(mediaobjects.Event, metaclass=XMLWrapper):
    __lookup__ = {}
    __wraps_type__ = ET.Element
    __default_data__ = ['Event']



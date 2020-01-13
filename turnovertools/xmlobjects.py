#!/usr/bin/env python3

from abc import ABCMeta
import xml.etree.ElementTree as ET

from . import mediaobject
from . import xmlparser

class XMLWrapper(ABCMeta):
    """
    Metaclass to create property attributes based on a lookup table of
    attribute names and XPath strings. Attribute and path pairs are
    taken from the __loopup__ class attribute.
    """
    def __new__(meta, name, bases, class_dict):
        """
        Assign getter and setter methods for each entry in __lookup__.
        """
        lookup = class_dict.get('__lookup__', {})
        for prop, target in lookup.items():
            if prop not in class_dict:
                class_dict[prop] = property(meta.getmapper(*target),
                                            meta.setmapper(*target))
        cls = type.__new__(meta, name, bases, class_dict)
        return cls

    def getmapper(path, attrib=None, attr='text'):
        """
        Generate getter method based using ETree XPATH support.
        """
        def getter(self):
            targets = self.data.findall(path)
            if len(targets) == 0:
                return None
            if len(targets) > 1:
                # Path that returns multiple results is poorly formed.
                # Might need to consider exceptions.
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

class XMLObject(object, metaclass=XMLWrapper):
    __wraps_type__ = ET.Element

    def _introspect(self):
        xmlparser.inspect_element(self.data, '', print)


class XMLTrack(mediaobject.SequenceTrack, XMLObject):
    __lookup__ = { 'title' : ('./ListHead/Title',),
                   'track_name' : ('./ListHead/Tracks',),
                   'framerate' : ('./ListHead/EditRate',)}
    __wraps_type__ = ET.Element
    __default_data__ = ['AssembleList']

    def __init__(self, data=None, **kwargs):
        super(XMLTrack, self).__init__(data=data, **kwargs)
        self.events = XMLEvent.wrap_list(
            self.data.iter('Event'), parent=self)


class XMLSequence(mediaobject.Sequence, XMLObject):
    __lookup__ = { 'date' : ('.', 'Date') }
    __wraps_type__ = ET.Element
    __default_data__ = ['FilmScribeFile']

    def __init__(self, data=None, **kwargs):
        super(XMLSequence, self).__init__(data=data, **kwargs)
        self.tracks = XMLTrack.wrap_list(
            self.data.iter('AssembleList'), parent=self)

    ##
    # Constructors
    @classmethod
    def fromfile(cls, filename):
        root = xmlparser.fromfile(filename)
        return cls.wrap_list([root])

    ##
    # Properties
    @property
    def title(self):
        if(len(self.tracks) > 0):
            return self.tracks[0].title
        else:
            return None

class XMLEvent(mediaobject.Event, XMLObject):
    __lookup__ = { 'event_num' : ('.', 'Num'),
                   'event_type' : ('.', 'Type'), 
                   'rec_start_tc' :
                       ('./Master/Start/Timecode/[@Type="TC1"]',), 
                   'rec_end_tc' : ('./Master/End/Timecode/[@Type="TC1"]',),
                   'rec_start_frame' : ('./Master/Start/Frame',),
                   'rec_end_frame' : ('./Master/End/Frame',),
                   'clip_name' : ('./Source/ClipName',),
                   'src_mob_id' : ('./Source/MobID',),
                   'src_start_tc' :
                       ('./Source/Start/Timecode/[@Type="Start TC"]',),
                   'src_end_tc' :
                       ('./Source/End/Timecode/[@Type="Start TC"]',),
                   'src_start_frame' : ('./Source/Start/Frame',),
                   'src_end_frame' :  ('./Source/End/Frame',),
                   'tape_name' : ('./Source/TapeName',),
                   'source_file' : ('./Source/SourceFile',), }
    __wraps_type__ = ET.Element
    __default_data__ = ['Event']

    ##
    # Constructors
    @classmethod
    def fromfile(cls, filename):
        """
        Create a list of XMLEvent objects directly from an XML file,
        discarding parent objects.
        """
        root = xmlparser.fromfile(filename)
        return cls.wrap_list(root.iter('Event'))
    
    def customs(self):
        for c in self.data.findall('./Source/Custom'):
            name = c.get('Name')
            value = c.text
            yield (name, value)

    def get_custom(self, custom):
        for name, value in self.customs():
            if name == custom:
                return value
        return None

    def set_custom(self, name, val):
        customs = self.data.findall('./Source/Custom')
        custom = None
        for c in customs:
            if c.get('Name') == name:
                custom = c
        if custom is None:
            custom = ET.SubElement(self._source, 'Custom')
            custom.attrib['Name'] = name
        custom.text = val

    @property
    def _source(self):
        source = self.data.find('Source')
        if source is None:
            source = ET.SubElement(self.data, 'Source')
        return source

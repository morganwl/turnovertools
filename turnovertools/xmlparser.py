#!/usr/bin/env python3

import re
import xml.etree.ElementTree as ET

def remove_control_characters(string):
    """Removes control characters and other funny business that will
    interfere with XML parser. Destructive."""
    return re.sub(r'[\x00-\x1F]+', '', string)

def fromfile(filename):
    """
    Instantiates and returns an ElementTree root object from an XML file.
    """
    with open(filename) as f:
        xml_string = f.read()
    xml_string = remove_control_characters(xml_string)
    return ET.fromstring(xml_string)

et_fromfile = fromfile

def inspect_root(root):
    print()
    for e in root:
        inspect_element(e)

def inspect_element(e, space='', func=print):
    indent = ' '
    func(space, '>', e.tag, e.text or '')
    for key, val in e.items():
        func(space+indent, '-', key, ':', val)
    for child in e:
        inspect_element(child, space+indent*2, func)

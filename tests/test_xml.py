#!/usr/bin/env python3

import logging
import os
import sys
import unittest

TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from turnovertools import xmlparser, xmlobjects

TEST_FILES = os.path.join(TEST_DIR, 'test_files')
TEST_XML_COMPLEX = os.path.join(TEST_FILES, 'R2-v29_Flattened.xml')

class TestOpenXML(unittest.TestCase):
    def setUp(self):
        pass

    def test_open_xml(self):
        self.assertIsNotNone(xmlparser.fromfile(TEST_XML_COMPLEX))

class TestParseXML(unittest.TestCase):
    def setUp(self):
        self.root = xmlparser.fromfile(TEST_XML_COMPLEX)
        # xmlparser.inspect_root(self.root)

def has_attrs_with_matching_values(mob, expected_attr_values):
    for key, value in expected_attr_values.items():
        if (key, getattr(mob, key)) != (key, value):
            return False
        
        
class TestXMLEvent(unittest.TestCase):
    def setUp(self):
        self.events = xmlobjects.XMLEvent.fromfile(TEST_XML_COMPLEX)
        self.events[15]._introspect()

    def test_parse_attributes(self):
        e0 = self.events[0]
        self.assertEqual(e0.event_num, '1')
        self.assertEqual(e0.event_type, 'Cut')
        self.assertEqual(e0.rec_start_tc, '00:59:58:00')
        self.assertEqual(e0.rec_end_tc, '00:59:58:00')
        self.assertEqual(e0.rec_start_frame, '0')
        self.assertEqual(e0.rec_end_frame, '0')
        self.assertEqual(e0.clip_name, 'CL_SLATE_23_976.mov')
        self.assertEqual(e0.src_mob_id, '060a2b340101010501010f10-13-00-00-00-{413389be-8575-a205-799f003ee1c23512}')
        self.assertEqual(e0.src_start_tc, '00:00:00:00')
        self.assertEqual(e0.src_end_tc, '00:00:00:00')
        self.assertEqual(e0.src_start_frame, '0')
        self.assertEqual(e0.src_end_frame, '0')
        self.assertEqual(e0.tape_name, 'CL_SLATE_23_976.mov')

        e1 = self.events[15]
        e1_expected_values = { 'event_num' : '16',
                               'event_type' : 'Cut',
                               'rec_start_tc' : '01:00:36:12',
                               'rec_end_tc' : '01:00:38:08',
                               'rec_start_frame' : '924',
                               'rec_end_frame' : '968',
                               'clip_name' : 'Ben archival montage',
                               'src_mob_id' : '060a2b340101010501010f10-13-00-00-00-{6d8b0a19-8758-a205-b22ed0817ad72f6a}',
                               'src_start_tc' : None,
                               'src_end_tc' : None,
                               'src_start_frame' : '0',
                               'src_end_frame' : '0',
                               'tape_name' : 'Signature Source Mob' }
        for key, value in e1_expected_values.items():
            self.assertEqual((key, getattr(e1, key)), (key, value))


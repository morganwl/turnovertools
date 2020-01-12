#!/usr/bin/env python3

import logging
import os
import sys
import unittest

TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from turnovertools import xmlparser, xmlobjects, mediaobject

TEST_FILES = os.path.join(TEST_DIR, 'test_files')
TEST_XML_COMPLEX = os.path.join(TEST_FILES, 'R2-v29_Flattened.xml')


def has_attrs_with_matching_values(mob, expected_attr_values):
    for key, value in expected_attr_values.items():
        if (key, getattr(mob, key)) != (key, value):
            return False


class TestOpenXML(unittest.TestCase):
    def setUp(self):
        pass

    def test_open_xml(self):
        self.assertIsNotNone(xmlparser.fromfile(TEST_XML_COMPLEX))


class TestParseXML(unittest.TestCase):
    def setUp(self):
        self.root = xmlparser.fromfile(TEST_XML_COMPLEX)

        
class TestXMLEvent(unittest.TestCase):
    def setUp(self):
        sequence = xmlobjects.XMLSequence.fromfile(TEST_XML_COMPLEX)[0]
        track1 = sequence[0]
        self.events = track1.events

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

    def test_get_custom(self):
        e1 = self.events[15] # this event has custom attributes
        for c in e1.customs():
            self.assertIsInstance(c, tuple)
        self.assertEqual(e1.get_custom('Link'), 'AE Composition')

    def test_get_parent(self):
        for i, e in enumerate(self.events):
            with self.subTest(i=i):
                self.assertIsInstance(e.parent, mediaobject.SequenceTrack)


class TestXMLSequence(unittest.TestCase):
    def setUp(self):
        self.sequence = xmlobjects.XMLSequence.fromfile(TEST_XML_COMPLEX)[0]

    def test_XMLSequence_fromfile(self):
        """Class method fromfile(filepath) of XMLSequence should create a
        list containing one valid Sequence object."""
        # root = xmlparser.fromfile(TEST_XML_COMPLEX)
        # xmlparser.inspect_root(root)
        sequences = xmlobjects.XMLSequence.fromfile(TEST_XML_COMPLEX)
        self.assertEqual(len(sequences), 1)
        self.assertIsInstance(sequences[0], mediaobject.Sequence)
    
    def test_parse_tracks(self):
        self.assertIsInstance(self.sequence.tracks, list)
        self.assertIsInstance(self.sequence.tracks[0],
                              mediaobject.SequenceTrack)

    def test_parse_attributes(self):
        expected_values = { 'date' : 'Oct. 25, 2008',
                            'title' : 'R2-v29_Flattened.NoGroups.Copy.01' }
        for key, value in expected_values.items():
            with self.subTest(key=key):
                self.assertEqual(getattr(self.sequence, key), value)

    def test_iter_sequence(self):
        for t in self.sequence:
            self.assertIsInstance(t, mediaobject.SequenceTrack)

    def test_index_sequence(self):
        self.assertIsInstance(self.sequence[0],
                              mediaobject.SequenceTrack)

    def test_len_sequence(self):
        self.assertEqual(len(self.sequence), 4)

    def test_track_order(self):
        # self.sequence._introspect()
        tracks_values = [ 'V1', 'V2', 'V3', 'V4' ]
        for t, name in zip(self.sequence, tracks_values):
            self.assertEqual(t.track_name, name)


class TestXMLTrack(unittest.TestCase):
    def setUp(self):
        self.sequence = xmlobjects.XMLSequence.fromfile(TEST_XML_COMPLEX)[0]
        self.track1 = self.sequence[0]
        self.track2 = self.sequence[1]
        self.track3 = self.sequence[2]
        self.track4 = self.sequence[3]

    def test_parse_attributes(self):
        t1 = self.track1
        t1_expected_values = { 
            'title' : 'R2-v29_Flattened.NoGroups.Copy.01',
            'track_name' : 'V1',
            'framerate' : '24'
        }
        for key, value in t1_expected_values.items():
            self.assertEqual( (key, getattr(t1, key)),
                              (key, value))
        
    def test_parse_events(self):
        t1 = self.track1
        self.assertIsInstance(t1.events, list)
        self.assertIsInstance(t1.events[0], mediaobject.Event)

    def test_iter_track(self):
        for e in self.track1:
            self.assertIsInstance(e, mediaobject.Event)

    def test_index_track(self):
        self.assertIsInstance(self.track1[0],
                              mediaobject.Event)

    def test_len_track(self):
        self.assertEqual(len(self.track1), 273)

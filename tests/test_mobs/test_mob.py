"""Tests the base media object classes."""

import unittest

import turnovertools.mediaobjects as mobs

class TestMobsUtility(unittest.TestCase):
    """Tests some utility functions in the mediaobjects subpackage."""
    def setUp(self):
        pass

    def test_conflicting_values(self):
        """Sends some different sets of values and makes sure that sets
        containing disparate values return True and sets containing
        values that evaluate to the same string return False."""
        self.assertTrue(mobs.mob.conflicting_values((1, 1, 2)))
        self.assertFalse(mobs.mob.conflicting_values(('a', None, 'a', 'a')))
        self.assertTrue(mobs.mob.conflicting_values((1, '1', 1)))

    def test_parse_framerate(self):
        """Given 3 values, a framerate primitive, and two timecodes,
        should be able to pull the framerate from either the primitive
        or the timecodes (if they are Timecode objects). Raises a
        ValueError if any framerates do not match."""
        self.assertEqual(mobs.Mob._parse_framerate('23.98', '01:00:00:00',
                                                   '01:00:10:00'), '23.98')

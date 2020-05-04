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

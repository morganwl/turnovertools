"""Test the Google mixin class."""

import unittest

from turnovertools import google
from turnovertools import mediaobjects as mobs

# pylint: disable=W0212

class TestGoogleMixin(unittest.TestCase):
    """Create various mobs classes mixed in with Google and confirm
    that their attributes work properly."""

    def setUp(self):
        class GoogleSourceClip(google.Google, mobs.SourceClip):
            """Test class"""
        self.test_object = GoogleSourceClip.dummy()

    def test_google_hasattrs(self):
        """Creates a SourceClip child class using the Google mixin and
        checks that it has all the attributes expected in both parent
        classes."""
        mob = self.test_object
        for attr in mobs.SourceClip.standard_attrs():
            self.assertTrue(hasattr(mob, attr))
        for attr in google.Google._provides_attrs:
            self.assertTrue(hasattr(mob, attr))

    def test_google_provides_attrs(self):
        mob = self.test_object
        parents_provide = list()
        parents_provide.extend(mobs.SourceClip.standard_attrs())
        parents_provide.extend(google.Google._provides_attrs)
        test_class_provides = dict.fromkeys(parents_provide, False)
        for attr in mob.standard_attrs():
            test_class_provides[attr] = True
        for attr in test_class_provides:
            self.assertTrue(test_class_provides[attr])

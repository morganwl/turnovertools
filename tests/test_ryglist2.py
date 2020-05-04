"""New TestSuites to guide the ryglist redesign. Separated from
test_ryglist for clarity."""

import unittest

from tests.test_sourcedb import get_source_db

from scripts import ryglist
from turnovertools import sourcedb

# continue running the TestRYGListAcceptance TestSuite until we have our
# own
from tests.test_ryglist import TestRYGListAcceptance

# rethinking the structure for ryglist
# abstractly, ryglist has the following functions:
# - export an image for every shot in an EDL, named according to the shot
# - export a video for every shot in an EDL, named according to the shot
# - export a table of all shots in the EDL, collated with additional source
#   metadata
# - attempt to gather source metadata from a variety of sources

# a fundamental flaw of ryglist is that it attempts to collect metadata from
# raw sources on every run.
# metadata needs to be stored separately in a sourcetable, which can be
# updated and maintained as needed.
# footage_tracker.csv performs some of this function, but we need to do
# better.
# we need FileMaker integration.

# so what are the elements of ryglist?
# - a sequence parser
#   - draw from edl library, but convert into our own mobs.Event object
# - a sequence frame/video extracter
# - a source table
#   - source table should have separate utilities for scraping information

# Development plan:
# Start by writing a source table module and replacing linkfinder

class TestGetSource(unittest.TestCase):
    """Should be able to supply a reel to the source table and
    get metadata back. For now, assume all sources are accessed by
    Tape/Source File interchangeably. Raise exception on missing
    source or multiple matching sources. Handle alternate names for
    the same source."""

    def setUp(self):
        self.test_file = get_source_db()
        self.source_table = sourcedb.SourceTable(sourcedb.connect(**self.test_file.kwargs))

    def tearDown(self):
        self.source_table.close()

    def test_get_link(self):
        """Queries source table with a reel name and expects the
        correct link back."""
        for reel, link in self.test_file.outputs.items():
            self.assertEqual(self.source_table[reel]['link'], link)

    def test_reel_not_found(self):
        """Queries source table with a missing reel and expects
        an Exception to be raised."""

    def test_multiple_matches(self):
        """Queries source table with a reel with multiple matches
        and expects an Exception to be raised."""
        # we might migrate this to creation of the source table, but
        # for now, we're assuming that the reel finding algorithm
        # might make some approximations to deal with variance in
        # Avid source name reporting

import unittest

from tests.common import SampleData
from turnovertools.adapters import AvidLog


class TestInput(unittest.TestCase):
    """Tests input of ALE."""

    def test_input(self):
        with open('/Volumes/GoogleDrive/My Drive/1015_Project Looking Glass/04_FILMMAKING_WORKING_FILES/TURNOVERS/RYG/200414_FC02/LG_20200414_FC02_RYG Reference Reels.ALE') as filehandle:
            ale = AvidLog.parse(filehandle)
        for row in ale:
            self.assertIsNotNone(row)

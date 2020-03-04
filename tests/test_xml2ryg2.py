

TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from scripts import xml2ryg2
from turnovertools import mediaobject

TEST_FILES = os.path.join(TEST_DIR, 'test_files')
TEST_EDL = '/Volumes/Looking Glass 1015_1/LookingGlass_WorkingMedia/TURNOVERS/RYG/200303_KP Cut/LG_R1_20200303_v34.Copy.01.edl'

class TestXml2ryg2Internals(unittest.TestCase):
    def setUp(self):
        self.input = TEST_EDL
        self.events = xml2ryg2.events_from_edl(TEST_EDL)

    def test_input_xml(self):
        events = xml2ryg.events_from_edl(TEST_EDL)
        for i, e in enumerate(events):
            with self.subTest(i=i):
                self.assertIsInstance(e, mediaobject.Event)

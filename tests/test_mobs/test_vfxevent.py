import unittest

import tests.shared_test_setup

from turnovertools.mediaobjects import Timecode
import turnovertools.mediaobjects as mobs

from tests.test_mobs import get_sample_event_data

def get_sample_vfxevent_data():
    event_data = get_sample_event_data()
    sample_data = dict(
        sequence_name='test_sequence',
        vfx_id='TEST_042_030',
        vfx_element='EL01',
        vfx_brief='Do tests',
        vfx_loc_tc=None, # we'll set this below
        vfx_loc_color='Yellow',
        frame_count_start='1009',
        scan_start_tc=None,
        scan_end_tc=None,
        scan_count_start=None)
    framerate = event_data['src_framerate']
    vfx_loc_tc = str((Timecode(framerate, event_data['src_end_tc']) -
                      Timecode(framerate, event_data['src_start_tc'])) // 2)
    sample_data['vfx_loc_tc'] = vfx_loc_tc
    event_data.update(sample_data)
    return event_data

class TestVFXEventInput(unittest.TestCase):
    def setUp(self):
        pass

    def test_vfxevent_creation_from_kwargs(self):
        sample_data = get_sample_vfxevent_data()
        vfxevent = mobs.VFXEvent(**sample_data)
        for attribute, val in sample_data.items():
            self.assertEqual(str(getattr(vfxevent, attribute)), str(val))

    def test_dummy_creation(self):
        sample_data = get_sample_vfxevent_data()
        vfxevent = mobs.VFXEvent.dummy()
        for attribute, val in sample_data.items():
            setattr(vfxevent, attribute, val)
            self.assertEqual(str(getattr(vfxevent, attribute)), str(val))
        vfxevent = mobs.VFXEvent.dummy(**sample_data)
        for attribute, val in sample_data.items():
            self.assertEqual(str(getattr(vfxevent, attribute)), str(val))

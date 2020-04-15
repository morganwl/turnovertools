from . import Timecode
from . import Event

class VFXEvent(Event):
    def __init__(self, vfx_id=None, vfx_element=None,
                 sequence_name=None, vfx_brief=None, vfx_loc_tc=None,
                 vfx_loc_color=None, frame_count_start=None,
                 scan_start_tc=None, scan_end_tc=None,
                 scan_count_start=None, **kwargs):
        super(VFXEvent, self).__init__(**kwargs)

        # cast to appropriate data types
        if vfx_loc_tc:
            vfx_loc_tc = Timecode(self.src_framerate, vfx_loc_tc)
        if frame_count_start is not None:
            frame_count_start = int(frame_count_start)
        if scan_start_tc is not None:
            scan_start_tc = Timecode(self.src_framerate, scan_start_tc)
        if scan_end_tc is not None:
            scan_end_tc = Timecode(self.src_framerate, scan_end_tc)
        if scan_count_start is not None:
            scan_count_start = int(scan_count_start)

        self.vfx_id = vfx_id
        self.vfx_element = vfx_element
        self.sequence_name = sequence_name
        self.vfx_brief = vfx_brief
        self.vfx_loc_tc = vfx_loc_tc
        self.vfx_loc_color = vfx_loc_color
        self.frame_count_start = frame_count_start
        self.scan_start_tc = scan_start_tc
        self.scan_end_tc = scan_end_tc
        self.scan_count_start = scan_count_start

    @property
    def vfx_id_element(self):
        buffer = [self.vfx_id, self.vfx_element]
        return '_'.join(filter(None, buffer))

    @classmethod
    def dummy(cls, **kwargs):
        defaults=dict(vfx_id='SLUG_010',
                      vfx_element='',
                      sequence_name='',
                      vfx_brief='',
                      vfx_loc_tc=None,
                      vfx_loc_color=None,
                      frame_count_start=1009)
        defaults.update(kwargs)
        return super(VFXEvent, cls).dummy(**defaults)

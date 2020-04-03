from timecode import Timecode

class Subcap(object):
    fps = '24'

    def __init__(self, tc_in, tc_out, caption):
        if not isinstance(tc_in, Timecode):
            tc_in = Timecode(self.fps, tc_in)
        if not isinstance(tc_out, Timecode):
            tc_out = Timecode(self.fps, tc_out)
        self.tc_in = tc_in
        self.tc_out = tc_out
        self.caption = caption

    def __str__(self):
        return(f'{self.tc_in} {self.tc_out}\n{self.caption}\n\n')

    @classmethod
    def write(cls, file, subcaps):
        with open(file, 'w') as fh:
            fh.write('@ This file written with subcap.py, version 0.0.1\n\n')
            fh.write('<begin subtitles>\n')
            for sub in subcaps:
                fh.write(f'{sub}')
            fh.write('<end subtitles>\n>')

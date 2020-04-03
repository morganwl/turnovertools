import io
import subprocess

import ffmpeg
from PIL import Image, ImageDraw, ImageFont
from timecode import Timecode

class Config:
    DEFAULT_SIZE = (1920, 1080)
    DEFAULT_FONT_FACE = '/Library/Fonts/Microsoft/Arial.ttf'
    DEFAULT_FONT_SIZE = 32

def blank_image(size = None):
    if size is None:
        size = Config.DEFAULT_SIZE
    return Image.new('RGBA', size, (255,255,255,0))

def draw_text(img, text, origin=(5,5), color=(255,255,255,255),
              face=None, font_size=None, align='left',
              rel_pos=None):
    if face is None:
        face = Config.DEFAULT_FONT_FACE
    if font_size is None:
        font_size = Config.DEFAULT_FONT_SIZE
    if rel_pos is not None:
        w_size, h_size = img.size
        w_rel, h_rel = rel_pos
        origin = (w_size * w_rel, h_size * h_rel)
    font = ImageFont.truetype(face, font_size)
    d = ImageDraw.Draw(img)
    d.text(origin, text, font=font, fill=(color), align=align)

def img_to_string(img):
    with io.BytesIO() as output:
        img.save(output, format="PNG")
        return output.getvalue()


class Watermark:
    displays = {}
    counters = {}
    
    def __init__(self, size=None, speed=None, **kwargs):
        """
        Initializes watermark for a particular shot
        """
        if size is None:
            size = Config.DEFAULT_SIZE
        if speed is None:
            speed = dict()
        self.speed = speed
        self.size = size
        for d in self.displays:
            setattr(self, d, kwargs[d])
        for c in self.counters:
            setattr(self, c, kwargs[c])
    
    def write_still(self):
        img = blank_image()
        for d, kwargs in self.displays.items():
            draw_text(img, str(getattr(self, d)), **kwargs)
        for c, kwargs in self.counters.items():
            draw_text(img, str(getattr(self, c)), **kwargs)
        return img_to_string(img)

    def write_string(self, dur):
        for i in range(dur):
            img = blank_image()
            for d, kwargs in self.displays.items():
                draw_text(img, str(getattr(self, d)), **kwargs)
            for c, kwargs in self.counters.items():
                draw_text(img, str(getattr(self, c) + i), **kwargs)
            yield img_to_string(img)

    def write_stream(self, dur, stream):
        for i in range(dur):
            img = blank_image()
            for d, kwargs in self.displays.items():
                draw_text(img, str(getattr(self, d)), **kwargs)
            for c, kwargs in self.counters.items():
                draw_text(img, str(getattr(self, c) + i), **kwargs)
            img.save(stream, format="PNG", compress_level=0)



class RecBurn(Watermark):
    displays = {
        'sequence_name': { 'rel_pos' : (.01, .01) }
        }
    counters = {
        'rec_tc_start' : { 'rel_pos' : (.01, .9) }
        }

if __name__ == '__main__':
    vin = '/Volumes/GoogleDrive/My Drive/1015_Project Looking Glass/04_FILMMAKING_WORKING_FILES/TURNOVERS/VFX/20200325_ARK Screening/LG_R2_20200325_VFX/LG_R2_20200325_v55_VFX Reference/LG_VFX_R2_010.mov'

    s = b''

    wm = RecBurn(sequence_name='test_seq',
                 rec_tc_start=Timecode(24, '01:00:00:00'))

    pipe = subprocess.Popen(['ffmpeg', '-y', '-i', vin, '-f', 'image2pipe',
                             '-framerate', '23.98', '-stream_loop', '0', 
                             '-i', '-', '-vcodec',
                             'libx264', '-pix_fmt', 'yuv420p',
                             '-filter_complex', 'overlay',  'test.mp4'],
                            stdin=subprocess.PIPE)
    wm.write_stream(138, pipe.stdin)

    pipe.stdin.close()
    pipe.wait()

import itertools
import io
import subprocess

import ffmpeg
from PIL import Image, ImageDraw, ImageFont
from timecode import Timecode

from . import fftools

class Config:
    DEFAULT_SIZE = (1920, 1080)
    DEFAULT_FONT_FACE = '/Library/Fonts/Arial Bold.ttf'
    DEFAULT_FONT_SIZE = 32

def color_string(ctuple):
    fontcolor = '0x'
    for c in ctuple:
        fontcolor += f'{c:02X}'
    return fontcolor

def blank_image(size = None):
    if size is None:
        size = Config.DEFAULT_SIZE
    return Image.new('RGBA', size, (255,255,255,0))

def draw_fftext(text, origin=(5,5), color=(255,255,255,255),
                face=None, font_size=None, align=('left', 'top'),
                rel_pos=None, box_width=None, box_height=None,
                box_fill=(0,0,0,0), size=None, counter=None):
    if size is None:
        size = Config.DEFAULT_SIZE
    if face is None:
        face = Config.DEFAULT_FONT_FACE
    if font_size is None:
        font_size = Config.DEFAULT_FONT_SIZE
    if rel_pos is not None:
        w_size, h_size = size
        w_rel, h_rel = rel_pos
        origin = (w_size * w_rel, h_size * h_rel)
    kwargs = {
        'fontcolor': color_string(color),
        'boxcolor': color_string(box_fill),
        'box': int(bool(box_width and box_height)),
        'text': text,
        'x': origin[0],
        'y': origin[1],
        'fontsize': font_size,
        'fontfile': face,
        }
    if isinstance(counter, Timecode):
        kwargs['timecode'] = str(counter).replace(':', ':')
        kwargs['rate'] = 24
    elif counter is not None and int(counter) == float(counter):
        print(counter)
        kwargs['text'] = '%{frame_num}'
        kwargs['start_number'] = counter
    return kwargs


def draw_fftext_str(text, origin=(5,5), color=(255,255,255,255),
                    face=None, font_size=None, align=('left', 'top'),
                    rel_pos=None, box_width=None, box_height=None,
                    box_fill=(0,0,0,0), size=None):
    if size is None:
        size = Config.DEFAULT_SIZE
    if face is None:
        face = Config.DEFAULT_FONT_FACE
    if font_size is None:
        font_size = Config.DEFAULT_FONT_SIZE
    if rel_pos is not None:
        w_size, h_size = size
        w_rel, h_rel = rel_pos
        origin = (w_size * w_rel, h_size * h_rel)
    fontcolor = color_string(color)
    boxcolor = color_string(box_fill)
    if box_width is not None and box_height is not None:
        box = 1
    else:
        box = 0
    return f'drawtext=text=\'{text}\':fontfile=\'{face}\':x={origin[0]}:y={origin[1]}:fontsize={font_size}:fontcolor={fontcolor}:box={box}:boxcolor={boxcolor}'

def draw_text(img, text, origin=(5,5), color=(255,255,255,255),
              face=None, font_size=None, align=('left', 'top'),
              rel_pos=None, box_width=None, box_height=None,
              box_fill=(0,0,0,0)):
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

    # get size of actual text box
    tw, th = d.textsize(text, font=font)
    # optionally draw background box
    if box_fill[3] > 0:
        if box_width is None:
            box_width = tw + 2
        if box_height is None:
            box_height = th + 2
        bx, by = align_origin(origin, box_width, box_height, align)
        d.rectangle((bx-1, by-1, bx + box_width - 1, by + box_height - 1), fill=box_fill)
    # adjust text origin to desired alignment
    origin = align_origin(origin, tw, th, align)
    d.text(origin, text, font=font, fill=(color))


def align_origin(origin, w, h, align=('left','top')):
    """Calculates size of text box and returns an origin as if aligned
    from the given origin.

    Accepted alignments are:
    left, center, right
    top, center, bottom"""
    if align==('left','top'):
        return origin

    aligns = {'left': 0, 'center': .5, 'right': 1, 'top': 0, 'bottom': 1}

    ox, oy = origin

    x_align, y_align = align
    return (ox - (w * aligns[x_align]), oy + (h * aligns[y_align]))

def img_to_string(img):
    with io.BytesIO() as output:
        img.save(output, format="PNG")
        return output.getvalue()

def framerate_to_float(framerate):
    try:
        framerate = float(framerate)
    except ValueError:
        dividend, divisor = framerate.split('/')
        framerate = int(dividend) / int(divisor)
    else:
        if framerate == 23.98:
            framerate = 23.976
    return framerate

def range_to_real_dur(start_tc, end_tc, framerate):
    frames = (end_tc - start_tc).frames
    framerate = framerate_to_float(framerate)
    return frames / framerate

def range_to_frames(start_tc, end_tc):
    return (end_tc - start_tc).frames

def build_ffmpeg_output(stream, outfile, dur, vcodec='libx264',
                        acodec='aac', pix_fmt='yuv420p', **kwargs):
    return (
        stream
        .output(outfile, to=str(dur), vcodec=vcodec, acodec=acodec,
                pix_fmt=pix_fmt, **kwargs)
        )

def build_ffmpeg_output_dnxhd(stream, outfile, dur, framerate, vbr, acodec='copy', **kwargs):
    return (
        stream
        .output(outfile, to=str(dur), vcodec='dnxhd', r=framerate,
                video_bitrate='36M', acodec=acodec, pix_fmt='yuv422p', **kwargs)
        )

def write_watermarks(videofile, watermarks, outfile=None,
                     start=0, end=None, duration=None,
                     scale=None, vcodec='libx264', acodec='aac'):

    # convert start Timecode to a fractional offset
    if isinstance(start, Timecode):
        ss = range_to_real_dur(videofile.src_start_tc, start,
                               videofile.framerate)
    else:
        ss = start
        
    # convert end Timecode to a fractional duration
    if isinstance(end, Timecode):
        dur = range_to_real_dur(start, end, videofile.framerate)
        dur_frames = range_to_frames(start, end)

    running_dur = dur
    stream = ffmpeg.input('pipe:', framerate=videofile.framerate)
    audio = ffmpeg.input(videofile.mediapath, ss=str(ss), t=str(dur))
    stream = ffmpeg.output(stream, audio, outfile, vcodec='copy', acodec='pcm_s16le', r=videofile.framerate)
    print(stream.compile())
    out_process = ffmpeg.run_async(stream, pipe_stdin=True,
                                   overwrite_output=True)
    for wm in watermarks:
        if wm.dur is not None:
            dur = wm.dur
        elif wm.rec_end_tc is not None:
            dur = range_to_real_dur(wm.rec_start_tc, wm.rec_end_tc, videofile.framerate)
        else:
            dur = running_dur
        wm_process = stream_video_with_watermark_text(videofile, wm, start=ss, duration=dur, scale=scale,
                                                      vcodec=vcodec)
        out_process.stdin.write(wm_process.stdout.read())
        wm_process.stdout.close()
        ss = ss + dur
        running_dur -= dur
    out_process.communicate()
    out_process.stdin.close()
    out_process.wait()
        


def stream_video_with_watermark_text(videofile, watermark, outfile=None,
                                     start=0, end=None, duration=None,
                                     scale=None, vcodec='libx264', acodec=None):

    # convert start Timecode to a fractional offset
    if isinstance(start, Timecode):
        ss = range_to_real_dur(videofile.src_start_tc, start,
                               videofile.framerate)
    else:
        ss = start
        
    # convert end Timecode to a fractional duration
    if isinstance(end, Timecode):
        dur = range_to_real_dur(start, end, videofile.framerate)
    else:
        dur = duration

    stream = ffmpeg.input(videofile.mediapath, ss=str(ss))
    for drawtext in watermark.write_drawtext():
        stream = stream.filter('drawtext', **drawtext)
    if vcodec == 'dnxhd':
        stream = build_ffmpeg_output_dnxhd(stream, 'pipe:', dur,
                                           videofile.framerate,
                                           videofile.bitrate,
                                           acodec='none', f='rawvideo')
    else:
        stream = build_ffmpeg_output(stream, 'pipe:', dur,
                                     vcodec, acodec='none', f='rawvideo')
    print(stream.compile())
    process = ffmpeg.run_async(stream, pipe_stdout=True, pipe_stderr=True)
    return process

def write_video_with_watermark_text(videofile, watermark, outfile=None,
                                    start=0, end=None, duration=None,
                                    scale=None, vcodec='libx264', acodec='aac'):
    # assign an output file
    if outfile is None:
        outfile = videofile.mediapath.rsplit('.', 1)[0] + '_watermark.mp4'

    # convert start Timecode to a fractional offset
    if isinstance(start, Timecode):
        ss = range_to_real_dur(videofile.src_start_tc, start,
                               videofile.framerate)
    else:
        ss = start
        
    # convert end Timecode to a fractional duration
    if isinstance(end, Timecode):
        dur = range_to_real_dur(start, end, videofile.framerate)
        dur_frames = range_to_frames(start, end)

    stream = ffmpeg.input(videofile.mediapath, ss=str(ss))
    for drawtext in watermark.write_drawtext():
        stream = stream.filter('drawtext', **drawtext)
    if vcodec == 'dnxhd':
        stream = build_ffmpeg_output_dnxhd(stream, outfile, dur,
                                           videofile.framerate,
                                           videofile.bitrate)
    else:
        stream = build_ffmpeg_output(stream, outfile, dur,
                                     vcodec, acodec)
    stream.run(overwrite_output=True)
    

def write_video_with_watermark(videofile, watermark, outfile=None,
                               start=0, end=None, duration=None,
                               scale=None, vcodec='libx264', acodec='aac'):
    # assign an output file
    if outfile is None:
        outfile = videofile.mediapath.rsplit('.', 1)[0] + '_watermark.mp4'

    # convert start Timecode to a fractional offset
    if isinstance(start, Timecode):
        ss = range_to_real_dur(videofile.src_start_tc, start,
                               videofile.framerate)
    else:
        ss = start
        
    # convert end Timecode to a fractional duration
    if isinstance(end, Timecode):
        dur = range_to_real_dur(start, end, videofile.framerate)
        dur_frames = range_to_frames(start, end)

    vid_node = ffmpeg.input(videofile.mediapath, ss=str(ss))
    wm_node = ffmpeg.input('pipe:', format='image2pipe', stream_loop=0)
    stream = ffmpeg.overlay(vid_node, wm_node)
    if vcodec == 'dnxhd':
        stream = build_ffmpeg_output_dnxhd(stream, outfile, dur,
                                           videofile.framerate,
                                           videofile.bitrate)
    else:
        stream = build_ffmpeg_output(stream, outfile, dur,
                                     vcodec, acodec)
    pipe = stream.run_async(pipe_stdin=True, quiet=True,
                            overwrite_output=True)
    if isinstance(watermark, list):
        running_dur = dur_frames
        for wm in watermark:
            if wm.dur is not None:
                dur_frames = wm.dur
            else:
                dur_frames = running_dur
            running_dur -= dur_frames
            wm.write_stream(dur_frames, pipe.stdin)
    else:
        watermark.write_stream(dur_frames, pipe.stdin)

    pipe.communicate()
    pipe.stdin.close()
    pipe.wait()


class Watermark:
    displays = {}
    counters = {}
    
    def __init__(self, size=None, speed=None, mob=None, dur=None, rec_end_tc=None, **kwargs):
        """
        Initializes watermark for a particular shot
        """
        if size is None:
            size = Config.DEFAULT_SIZE
        if speed is None:
            speed = dict()
        self.speed = speed
        self.size = size
        self.dur = dur
        self.rec_end_tc = rec_end_tc
        # iter through displays and then counters
        for field in itertools.chain(self.displays, self.counters):
            # kwargs override any mob attributes
            if field in kwargs:
                val = kwargs[field]
            else:
                try:
                    val = getattr(mob, field)
                except AttributeError:
                    raise Exception(f'{field} not given in kwargs and no mob provided.')
            setattr(self, field, val)
    
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

    def write_drawtext(self):
        filters = list()
        for d, kwargs in self.displays.items():
            filters.append(draw_fftext(str(getattr(self, d)), **kwargs))
        for c, kwargs in self.counters.items():
            filters.append(draw_fftext('', counter=getattr(self, c), **kwargs))
        return filters


class VFXReference(Watermark):
    displays = {
        'vfx_id' : {'rel_pos' : (.01, .01), 'box_fill': (0,0,0,64),
                    'font_size': 48},
        'vfx_brief' : {'rel_pos': (.5, .01),
                       'align': ('center', 'top'),
                       'box_fill': (0,0,0,64),
                       'font_size': 48},
        'vendor': { 'rel_pos': (.75, .8),
                    'align': ('center', 'top'),
                    'color' : (255, 255, 255, 92),
                    'font_size': 64,
                    },
        'property': { 'rel_pos': (.2, .9),
                      'align': ('center', 'top'),
                      'color': (255, 255, 255, 92),
                      'font_size': 64,
                      }
        }
    counters = {
        'frame_count_start' : {'rel_pos': (.92, .95),
                               'align': ('right', 'top'),
                               'box_fill': (0,0,0,64),
                               'font_size': 48},
        'rec_start_tc' : {'rel_pos': (.01, .95), 'box_fill': (0,0,0,64),
                          'font_size': 48},
        }

class RecBurn(Watermark):
    displays = {
        'sequence_name': { 'rel_pos' : (.01, .01) }
        }
    counters = {
        'rec_start_tc' : { 'rel_pos' : (.01, .9) }
        }

class RecBurnWatermark(Watermark):
    displays = {
        'vendor': { 'rel_pos': (.75, .8),
                    'align': ('center', 'top'),
                    'color' : (255, 255, 255, 92),
                    'font_size': 64,
                    },
        'property': { 'rel_pos': (.2, .9),
                      'align': ('center', 'top'),
                      'color': (255, 255, 255, 92),
                      'font_size': 64,
                      }
                      
        }
    counters = {
        'rec_start_tc' : { 'rel_pos': (.01, .95), 'box_fill': (0,0,0,64),
                           'font_size': 48}
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

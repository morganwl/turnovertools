#!/usr/bin/env python3

import datetime
from heapq import heappush, heappop
import itertools
import numpy as np
import os
import subprocess
import signal
import sys
import time
from timeit import timeit

import cv2
import ffmpeg
from skimage.measure import compare_ssim as ssim
from timecode import Timecode

from turnovertools import fftools

##
# Close any asynchronous subprocesses on sigint

def handle_sigint(signum, frame):
    fr = frame
    while fr is not None:
        for var, value in fr.f_locals.items():
            print(var, ':', type(value))
        fr = fr.f_back
    sys.exit()

# signal.signal(signal.SIGINT, handle_sigint)

##
# ffmpeg functions

def build_ffmpeg(vid, frameno=0, format='image2', dur=None,
    scale=None, interval=1, ss=None, **kwargs):
    input_args = {}
    if ss is not None:
        input_args['ss'] = ss
    command = ffmpeg.input(vid, **input_args)
    output_args = { 'format': format,
                    'vcodec': 'bmp' }
    if dur is not None:
        output_args['vframes'] = dur
    for key, value in kwargs.items():
        output_args[key] = value
    if interval > 1:
        command = ffmpeg.filter(command, 'select',
                                'not(mod(n,{}))'.format(interval))
        output_args['vsync'] = 0
    if scale is not None:
        width, height = scale
        aspect = width / height
        command = (
            ffmpeg
            .filter(command, 'pad', h='iw/{}'.format(aspect), y='(oh-ih)/2')
            .filter('scale', '{}x{}'.format(width, height))
        )
    command = ffmpeg.output(command, 'pipe:', **output_args)
    return command

def extract_frame(vid, frameno=0, format='image2',
                       dur=None, scale=None, interval=1, **kwargs):
    command = build_ffmpeg(vid, frameno=frameno, format=format, dur=1,
                           scale=scale, **kwargs)
    frame, _ = ffmpeg.run(command, capture_stdout=True, capture_stderr=True)
    return frame

def frame_iterator(process, size):
    while True:
        img = process.stdout.read(size)
        if not img:
            break
        yield img

def interval_stream_frames(vid, interval=2, probe=None, **kwargs):
    if probe is None:
        probe = ffmpeg.probe(vid)
    vidinfo = next((stream for stream in probe['streams'] if 
                    stream['codec_type'] == 'video'), None)
    fps = vidinfo['r_frame_rate']
    try:
        fps = float(fps)
    except ValueError:
        left, right = fps.split('/')
        fps = float(left) / float(right)
    ss_interval = interval / fps
    if 'nb_frames' in vidinfo:
        nb_frames = int(vidinfo['nb_frames'])
    else:
        nb_frames = int(fps * float(vidinfo['duration']))
    if nb_frames < interval:
        yield extract_frame(vid, **kwargs)
        return
    for i in range(nb_frames // interval):
        yield extract_frame(vid, ss=ss_interval*i, **kwargs)

def stream_frames(vid, size=None, frameno=0, dur=None, format='image2pipe',
                      scale=None, **kwargs):
    command = build_ffmpeg(vid, frameno=frameno, format=format,
                           dur=dur, scale=scale, **kwargs)
    if size is None:
        size = len(extract_frame(vid, scale=scale, **kwargs))
    process = ffmpeg.run_async(command, pipe_stdout=True,
                               pipe_stderr=True)
    try:
        yield from frame_iterator(process, size)
    finally:
        print('Calling cleanup.')
        process.communicate()

def probe_clip(video):
    """Probes a video file and returns a clip object with various
    metadata."""
    clip = lambda: None
    clip.mediapath = video
    probe = ffmpeg.probe(video)
    vid_stream = next(stream for stream in probe['streams'] if
                      stream['codec_type'] == 'video')
    clip.framerate = vid_stream['r_frame_rate']
    clip.duration = Timecode(clip.framerate,
                             start_seconds=float(probe['format']['duration']))
    if 'timecode' in probe['format']['tags']:
        clip.src_start_tc = Timecode(
            clip.framerate, probe['format']['tags']['timecode'])
    else:
        clip.src_start_tc = Timecode(clip.framerate, '00:00:00:00')
    clip.src_end_tc = clip.src_start_tc + clip.duration
    width = vid_stream['width']
    height = vid_stream['height']
    clip.scale = (int(width), int(height))
    aw, ah = vid_stream['display_aspect_ratio'].split(':')
    clip.aspect_ratio = float(aw) / float(ah)
    clip.bitrate = int(probe['format']['bit_rate'])
    return clip

def probe_timecode(video):
    """Probes a video file and returns the timecode as a Timecode object."""
    probe = ffmpeg.probe(video)
    tc_string = probe['format']['tags']['timecode']
    vid_streams = next(stream for stream in probe['streams'] if
                       stream['codec_type'] == 'video')
    fr = vid_streams['r_frame_rate']
    return Timecode(fr, tc_string)

##
# frame processing functions

def compare(image, other):
    image = cvdecode(image)
    other = cvdecode(other)
    return ssim(image, other, multichannel=True)

def mse(image, other):
    image = cvdecode(image)
    other = cvdecode(other)
    err = np.sum((image.astype('float') - other.astype('float')) ** 2)
    err /= float(image.shape[0] * other.shape[1])
    return err
    
def cvdecode(image):
    image = np.frombuffer(image, dtype='uint8')
    image = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
    return image

##
# search functions

def find_frame(frame, vid, interval=1, threshold=150):
    min = None
    match = None
    i = 0
    for i, candidate in enumerate(vid):
        err = mse(frame, candidate)
        if min is None or err < min:
            min = err
            match = candidate
            if err <= threshold:
                break
    return min, match

def find_in_dir(src, basepath, frame_num=0, pix_fmt='gray9be',
    scale=(960,540), interval=64):
    goal = extract_frame(src, scale=scale, pix_fmt=pix_fmt)
    matches = []
    for dirpath, dirs, files in os.walk(basepath):
        start = time.time()
        print('Searching directory {} containing {} files.'.
              format(dirpath, len(files)))
        for candidate in (os.path.join(dirpath, x) for x in files):
            try:
                probe = ffmpeg.probe(candidate)
            except ffmpeg.Error:
                continue
            if interval > 1:
                video = interval_stream_frames(candidate,
                                               interval=interval,
                                               probe=probe,
                                               scale=scale,
                                               pix_fmt=pix_fmt)
            else:
                video = stream_frames(candidate, scale=scale,
                                      pix_fmt=pix_fmt)
            err, match = find_frame(goal, video)
            if match is None:
                continue
            try:
                heappush(matches, (err,candidate,match))
            except TypeError:
                print(err, candidate, len(match))
        print('Searched in {} seconds.'.format(time.time() - start))
    while len(matches) > 0:
        yield heappop(matches)

def search_report(src, basepath, outpath, **kwargs):
    start = datetime.datetime.today()
    reportpath = os.path.join(outpath, 'search_report_{}{:02}{:02}-{:02}{:02}.txt'.
                              format(start.year, start.month,
                                     start.day, start.hour,
                                     start.minute))
    search = find_in_dir(src, basepath, **kwargs)
    for i, (err, matchpath, img) in enumerate(search):
        imgpath = os.path.join(outpath,
                               'result_{:08}_{:.2f}.bmp'.format(i, err))
        with open(imgpath, 'wb') as fh:
            fh.write(img)
        with open(reportpath, 'at') as fh:
            fh.write('{:08},{:.2f},{}\n'.format(i, err, matchpath))
    return reportpath

def profile():
    sample = '/Volumes/sync.Cocoon-3_1/Cocoon_Camera Masters/20160408/4-8-2016 5A Mural Wall/Drone Camera/Drone Roll 2/DJI_0036.MOV'
    print(timeit(lambda: list(stream_frames(sample, pix_fmt='gray9be',
    scale=(960,540))), number=1))
    print(timeit(lambda: list(stream_frames(sample, scale=(1920,1080))), number=1))

if __name__ == '__main__':
    src = sys.argv[1]
    searchpath = sys.argv[2]
    outpath = sys.argv[3]
    search_report(src, searchpath, outpath, interval=1)

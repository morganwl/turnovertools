#!/usr/bin/env python3

import os
import sys

import edl
from timecode import Timecode

from turnovertools import fftools, vfxlist, watermark, Config

def read_csv(inputfile):
    rows = list()
    with open(inputfile, newline='') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows

def index_videos(basedir):
    video_index = dict()
    for dirpath, dirnames, filenames in os.walk(basedir):
        for fn in filenames:
            if fn.endswith('.mov') or fn.endswith('.mp4') \
                    or fn.endswith('.mxf'):
                basename, ext = os.path.splitext(fn)
                if basename in video_index:
                    raise Exception('Multiple video files found for ' + basename)
                video_index[basename] = os.path.join(dirpath, fn)
    return video_index


def main(csvfile, mediadir, outputdir):
    # mock up desired output first!
    mock_dir = '/Users/morgan/private_test_files/turnovertools/vfx/control_samples/LG_VFX_R2_REFERENCE'

    # step through vfx shots and output a video with watermarks for each
    reel_index = index_videos(mediadir)
    vfx_shots = vfxlist.read_vfx_csv(csvfile)
    for vfx in vfx_shots:
        vfpath = reel_index[vfx['sequence_name']]
        vf = fftools.probe_clip(vfpath)
        outfile = os.path.join(outputdir, vfx['vfx_id'] + '.mov')
        vfx['rec_start_tc'] = Timecode(vf.framerate, vfx['rec_start_tc'])
        vfx['rec_end_tc'] = Timecode(vf.framerate, vfx['rec_end_tc'])
        vfx['frame_count_start'] = int('frame_count_start'])
        start = vfx['rec_start_tc']
        end = vfx['rec_end_tc']
        wm = watermark.VFXReference(**vfx)
        watermark.write_video_with_watermark(vf, wm, outfile=outfile,
                                             start=start,
                                             end=end,
                                             vcodec='dnxhd',
                                             acodec='none')

#    for fn in (vfx['vfx_id'].strip() + '.mov' for vfx in vfx_shots):
#        with open(os.path.join(mock_dir, fn), 'rb') as in_vid, \
#                open(os.path.join(outputdir, fn), 'wb') as out_vid:
#            out_vid.write(in_vid.read())
    

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])

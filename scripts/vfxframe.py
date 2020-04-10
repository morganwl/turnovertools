#!/usr/bin/env python3

"""Reads a set of EDLs or a CSV and, given a matching videofile,
outputs a reference still for every VFX marker."""

from collections import defaultdict
import os
import sys

from timecode import Timecode

from turnovertools import interface, vfxlist, Config, output

def main(inputpath, mediadir=None, outputdir=None):
    # figure out the various inputs
    input = interface.Input(inputpath, mediadir, outputdir)
    input.csv_file = inputpath
    input.mixdowns = dict()
    input.mixdowns['LG_R2_20200325_v55_conform prep'] = '/Volumes/GoogleDrive/My Drive/1015_Project Looking Glass/04_FILMMAKING_WORKING_FILES/TURNOVERS/Reels_Clean SameAsSource/LG_R2_20200325_v55.mxf'
    input.outputdir = '/Users/morgan/Desktop'

    # if it's an EDL, parse the EDL

    # if it's a CSV, parse the CSV
    # let's start with the CSV, because it works with FMP and our
    # existing Avid pipeline
    if input.csv_file:
        vfx_elements = vfxlist.read_vfx_csv(input.csv_file)
    
    # use our video output tools from xml2ryg2 to export framegrabs
    frame_codes = defaultdict(list)
    for el in vfx_elements:
        rec_tc = (Timecode(24, el['vfx_loc_tc']) - Timecode(24, el['src_start_tc']) + Timecode(24, el['rec_start_tc']))
        frame_codes[el['sequence_name']].append(rec_tc)
    for source, frames in frame_codes.items():
        print(frames)
        vf = output.VideoFile(input.mixdowns[source])
        for i, frame in enumerate(vf.stream_frames(frames)):
            with open(os.path.join(input.outputdir, str(i) + '.jpg'), 'wb') as fh:
                fh.write(frame)

if __name__ == '__main__':
    main(*sys.argv[1:])

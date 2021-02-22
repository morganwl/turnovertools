from collections import namedtuple
import csv
import os
import sys

from timecode import Timecode

from turnovertools import fftools, vfxlist, watermark, Config

VENDOR = 'FrameStore'
PROPERTY = 'Property of ABC Signature Studios'

VFXRow = namedtuple('VFXRow', ('vfx_id', 'vfx_brief', 'rec_start_tc',
                               'rec_end_tc', 'frame_count_start',
                               'context_start', 'context_end', 
                               'videofile'))

def range_to_real_dur(start_tc, end_tc, framerate):
    frames = (end_tc - start_tc).frames
    framerate = framerate_to_float(framerate)
    return frames / framerate

def read_csv(inputfile):
    rows = list()
    with open(inputfile, newline='') as fh:
        reader = csv.reader(fh)
        for row in reader:
            rows.append(VFXRow(*row))
    return rows

def build_batches(vfx, framerate):
    batches = list()
    b = dict()
    wm = None

    for shot in vfx:
        shot = shot._asdict()
        shot['rec_start_tc'] = Timecode(framerate, shot['rec_start_tc'])
        shot['rec_end_tc'] = Timecode(framerate, shot['rec_end_tc'])
        shot['context_start'] = Timecode(framerate, shot['context_start'])
        shot['context_end'] = Timecode(framerate, shot['context_end'])

        if wm:
            b['watermarks'].append(wm)
            # add filler between VFX shots
            if shot['context_start'].frames <= b['end'].frames:
                b['end'] = shot['context_end']
                b['name'] = shot['vfx_id'].rsplit('_', 1)[0]
            if wm.rec_end_tc != shot['rec_start_tc']:
                if b['end'] == shot['context_end']:
                    b['watermarks'].append(watermark.RecBurnWatermark(
                            vendor=VENDOR,
                            property=PROPERTY,
                            sequence_name=b['name'],
                            rec_start_tc=wm.rec_end_tc,
                            rec_end_tc=shot['rec_start_tc']))
                else:
                    b['watermarks'].append(watermark.RecBurnWatermark(
                            vendor=VENDOR,
                            property=PROPERTY,
                            rec_start_tc=wm.rec_end_tc,
                            sequence_name=b['name'],
                            rec_end_tc=b['end']))
                    batches.append(b)
                    b = dict()
        if len(b) == 0:
            b['start'] = shot['context_start']
            b['end'] = shot['context_end']
            b['videofile'] = fftools.probe_clip(shot['videofile'])
            b['name'] = shot['vfx_id']
            b['watermarks'] = list()
            b['watermarks'].append(watermark.RecBurnWatermark(
                            vendor=VENDOR,
                            property=PROPERTY,
                            sequence_name=b['name'],
                            rec_start_tc=b['start'],
                            rec_end_tc=shot['rec_start_tc']))
        wm = watermark.VFXReference(**shot, vendor=VENDOR, property=PROPERTY)

    if wm:
        b['watermarks'].append(wm)
        if b['end'] != wm.rec_end_tc:
            b['watermarks'].append(watermark.RecBurnWatermark(
                    vendor=VENDOR,
                    property=PROPERTY,
                    rec_start_tc=wm.rec_end_tc,
                    rec_end_tc=b['end'],
                    sequence_name=b['name']))
        batches.append(b)
    return batches
    
def main(vfxlist, outdir):
    vfx = read_csv(vfxlist)
    batches = build_batches(vfx, '23.98')
    for i, b in enumerate(batches):
        outfile = f"{i:02}_{b['name']}.mov"
        print(f'Writing {outfile}')
        watermark.write_watermarks(b['videofile'], b['watermarks'],
                                   outfile=os.path.join(outdir, outfile),
                                   start=b['start'],
                                   end=b['end'],
                                   vcodec='dnxhd')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

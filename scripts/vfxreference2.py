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
                               'context_start', 'context_end', 'vendor',
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

def build_batches_single(vfx, framerate):
    """Takes a VFX list and returns a list of batches of Watermark
    objects, where each batch is a continuous stretch of source
    video. Each batch contains only one VFX shot, with context before
    and after."""
    batches = list()
    wm = None

    for shot in vfx:
        batch = dict()
        shot = shot._asdict()
        shot['rec_start_tc'] = Timecode(framerate, shot['rec_start_tc'])
        shot['rec_end_tc'] = Timecode(framerate, shot['rec_end_tc'])
        shot['context_start'] = Timecode(framerate, shot['context_start'])
        shot['context_end'] = Timecode(framerate, shot['context_end'])
        batch['watermarks'] = list()
        
        # adjust poorly formed context_start
        if shot['context_start'].frames > shot['rec_start_tc'].frames:
                shot['context_start'] = shot['rec_start_tc'] - 48
        batch['start'] = shot['context_start']
        if shot['context_end'].frames < (shot['rec_end_tc'].frames + 48):
            shot['context_end'] = shot['rec_end_tc'] + 48
        batch['end'] = shot['context_end']
        batch['name'] = shot['vfx_id']
        batch['videofile'] = fftools.probe_clip(shot['videofile'])

        batch['watermarks'].append(watermark.RecBurnWatermark(
                vendor=shot['vendor'],
                property=PROPERTY,
                sequence_name=batch['name'],
                rec_start_tc=batch['start'],
                rec_end_tc=shot['rec_start_tc']))
        batch['watermarks'].append(watermark.VFXReference(**shot,
                property=PROPERTY))
        batch['watermarks'].append(watermark.RecBurnWatermark(
                vendor=shot['vendor'],
                property=PROPERTY,
                sequence_name=batch['name'],
                rec_start_tc=shot['rec_end_tc'],
                rec_end_tc=batch['end']))
        batches.append(batch)
    return batches
        
def build_batches_all(vfx, framerate):
    """Takes a VFX list and returns a single batch of Watermark objects
    running from the first context_start to the last context_end."""
    b = dict()
    wm = None

    # initialize b[start]
    # for shot in vfx
    # - if wm.rec_end_tc != shot[rec_start_tc]
    # - - add filler
    # - add shot watermark
    # - extend b[end]
    # add final filler
    # return

    for shot in vfx:
        shot = shot._asdict()
        shot['rec_start_tc'] = Timecode(framerate, shot['rec_start_tc'])
        shot['rec_end_tc'] = Timecode(framerate, shot['rec_end_tc'])
        shot['context_start'] = Timecode(framerate, shot['context_start'])
        shot['context_end'] = Timecode(framerate, shot['context_end'])

        if wm:
            b['watermarks'].append(wm)
            # add filler between VFX shots
            b['end'] = shot['context_end']
            if wm.rec_end_tc != shot['rec_start_tc']:
                if b['end'] == shot['context_end']:
                    b['watermarks'].append(watermark.RecBurnWatermark(
                            vendor=shot['vendor'],
                            property=PROPERTY,
                            sequence_name=b['name'],
                            rec_start_tc=wm.rec_end_tc,
                            rec_end_tc=shot['rec_start_tc']))
                else:
                    b['watermarks'].append(watermark.RecBurnWatermark(
                            vendor=shot['vendor'],
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
                            vendor=shot['vendor'],
                            property=PROPERTY,
                            sequence_name=b['name'],
                            rec_start_tc=b['start'],
                            rec_end_tc=shot['rec_start_tc']))
        wm = watermark.VFXReference(**shot, property=PROPERTY)

    if wm:
        b['watermarks'].append(wm)
        if b['end'] != wm.rec_end_tc:
            b['watermarks'].append(watermark.RecBurnWatermark(
                    vendor=shot['vendor'],
                    property=PROPERTY,
                    rec_start_tc=wm.rec_end_tc,
                    rec_end_tc=b['end'],
                    sequence_name=b['name']))
        batches.append(b)
    return batches


def build_batches(vfx, framerate):
    """Takes a VFX list and returns a list of batches of Watermark
    objects, where each batch is a continuous stretch of source
    video. Greedily groups batches, joining continuous video wherever
    possible."""
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
            if shot['context_start'].frames > shot['rec_start_tc'].frames:
                shot['context_start'] = shot['rec_start_tc'] - 48
            if shot['context_start'].frames <= b['end'].frames:
                b['end'] = shot['context_end']
                b['name'] = shot['vfx_id'].rsplit('_', 1)[0]
            if wm.rec_end_tc != shot['rec_start_tc']:
                if b['end'] == shot['context_end']:
                    b['watermarks'].append(watermark.RecBurnWatermark(
                            vendor=shot['vendor'],
                            property=PROPERTY,
                            sequence_name=b['name'],
                            rec_start_tc=wm.rec_end_tc,
                            rec_end_tc=shot['rec_start_tc']))
                else:
                    b['watermarks'].append(watermark.RecBurnWatermark(
                            vendor=shot['vendor'],
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
                            vendor=shot['vendor'],
                            property=PROPERTY,
                            sequence_name=b['name'],
                            rec_start_tc=b['start'],
                            rec_end_tc=shot['rec_start_tc']))
        wm = watermark.VFXReference(**shot, property=PROPERTY)

    if wm:
        b['watermarks'].append(wm)
        if b['end'] != wm.rec_end_tc:
            b['watermarks'].append(watermark.RecBurnWatermark(
                    vendor=shot['vendor'],
                    property=PROPERTY,
                    rec_start_tc=wm.rec_end_tc,
                    rec_end_tc=b['end'],
                    sequence_name=b['name']))
        batches.append(b)
    return batches

def main_single(vfxlist, outdir):
    vfx = read_csv(vfxlist)
    batches = build_batches_single(vfx, '23.98')
    for i, b in enumerate(batches):
        outfile = f"{i:02}_{b['name']}.mov"
        print(f'Writing {outfile}')
        watermark.write_watermarks(b['videofile'], b['watermarks'],
                                   outfile=os.path.join(outdir, outfile),
                                   start=b['start'],
                                   end=b['end'],
                                   vcodec='dnxhd')
    
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
    if len(sys.argv) > 3 and sys.argv[3] == '--group':
        main(sys.argv[1], sys.argv[2])
    else:
        main_single(sys.argv[1], sys.argv[2])

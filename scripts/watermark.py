import os
import sys

from turnovertools import fftools, watermark, Config
#from turnovertools.mediaobjects import MediaFile

def main(infile, wm_text, outfile=None, vcodec = 'dnxhd', 
         acodec='copy'):
    """
    """
    if outfile is not None:
        if os.path.isdir(outfile):
            outfile = os.path.join(outfile, infile)
        else:
            pass
    else:
        root, ext = os.path.splitext(infile)
        outfile = root + '_watermark' + ext
    vf = fftools.probe_clip(infile)
    wm = watermark.RecBurnWatermark(sequence_name=infile, 
                                    watermark=wm_text,
                                    rec_start_tc=vf.src_start_tc)
    watermark.write_video_with_watermark(vf, wm, outfile=outfile,
                                         start=vf.src_start_tc,
                                         end=vf.src_end_tc)

if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:5])

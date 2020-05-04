import os
import sys

import turnovertools.mediaobjects as mobs
from turnovertools import sourcedb
from turnovertools.adapters import AvidLog
from turnovertools import mxfdb

def main(inputfile):
    db = mxfdb.open(os.path.join(os.path.expanduser("~"), '.mxfdb.db'))
    with open(inputfile) as filehandle:
        avidlog = AvidLog.parse(filehandle)
    for row in avidlog:
        clip = mobs.SourceClip(row.to_mobs_dict())

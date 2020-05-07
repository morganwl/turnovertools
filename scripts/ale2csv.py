#!/usr/bin/env python3

"""
Reads an Avid ALE and converts it to a csv for FileMaker input.

usage: ale2csv.py <ale file> [outputfile|':temp:']

ALE can be any valid, Avid-generated ALE file. The field names of the ALE
will be translated to the universal mobs naming convention, and then output
to csv. Currently, the fields output will be those used in the Google
Creative Labs workflow, but this could be quickly changed by supplying
a new mobs class to the avidlog.write_csv method, or skipping the
"columns" option altogether, which would write all fields contained
in the ALE.
"""

# tests checklist:
# - test temporary file output
# - acceptance test

import sys
import tempfile

from turnovertools import adapters
from turnovertools.google import GoogleSourceClip

# TO-DO: Break out into a couple sub-methods?
def main(inputfile, outputfile=None):
    """Main program function."""
    with open(inputfile) as filehandle:
        avidlog = adapters.AvidLog.parse(filehandle)
    if outputfile == ':temp:':
        filehandle = tempfile.NamedTemporaryFile(mode='wt', suffix='.csv',
                                                 delete=False, newline='')
        outputfile = filehandle.name
    else:
        filehandle = open(outputfile, 'wt', newline='')
    avidlog.write_csv(filehandle, columns=GoogleSourceClip.standard_attrs())
    filehandle.close()
    print(outputfile)

if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])

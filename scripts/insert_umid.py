#!/usr/bin/env python3

"""
Receive a command line argument of a reel and a FileMaker record id.
Query mxf database for a matching mediafile and, if found, insert a
thumbnail into the FileMaker at the matching id.
"""
# TO-DO: Write tests to actually outline implementation of this program

import csv
import os
import sys

import turnovertools.mediaobjects as mobs
from turnovertools import sourcedb
from turnovertools import mxfdb
from turnovertools.config import Config

def insert_umid(reel, primary_key, table, sourcetable, mediadb):
    umids = list(mediadb.get_umids(reel, 'video'))
    if not umids:
        return

    # get mxf file path
    mediafile = mobs.MediaFile.probe(umids[0].path)
    mediafile.poster_frame = sourcetable.get_pk(primary_key)['poster_frame']
    thumbnail = mediafile.thumbnail()
    sourcetable.update_container(primary_key, 'image', thumbnail,
                                 f'{mediafile.clip_name}.jpg', pk=True)
    sourcetable.update(primary_key, 'umid', mediafile.umid, pk=True)

def main(reel, primary_key, table, sourcetable, mediadb=None):
    """Queries the mxf database for mediafiles matching reel. If found,
    inserts the umid and a thumbnail into the record referenced by
    primary_key in the sourcetable. sourcetable can be provided as a
    database name (as available through ODBC) or a SourceTable object.
    mxfdb can either be a path to an sqlite3 file or a MediaDatabase
    object."""
    # initialize database objects if necessary
    if mediadb is None:
        mediadb = mxfdb.open(Config.MXFDB)
    elif isinstance(mxfdb, str):
        mediadb = mxfdb.open(mxfdb)
    if isinstance(sourcetable, str):
        sourcetable = sourcedb.SourceTable(sourcedb.connect(database=sourcetable))

    # first argument can either be a reel or a file containing a list of reels
    if os.path.isfile(reel):
        with open(reel, newline='') as filehandle:
            reader = csv.reader(filehandle)
            sources = list(reader)
    else:
        sources = [(reel, primary_key)]

    for source in sources:
        print(source)
        insert_umid(source[0], source[1], table, sourcetable, mediadb)

if __name__ == '__main__':
    main(*sys.argv[1:])

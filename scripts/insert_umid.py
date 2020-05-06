"""
Receive a command line argument of a reel and a FileMaker record id.
Query mxf database for a matching mediafile and, if found, insert a
thumbnail into the FileMaker at the matching id.
"""
# TO-DO: Write tests to actually outline implementation of this program

import sys

import turnovertools.mediaobjects as mobs
from turnovertools import sourcedb
from turnovertools import mxfdb
from turnovertools.config import Config

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
    umids = list(mediadb.get_umids(reel, 'video'))
    # get mxf file path
    mediafile = mobs.MediaFile.probe(umids[0].path)
    thumbnail = mediafile.thumbnail()
    sourcetable.update_container(reel, 'image', thumbnail,
                                 f'{mediafile.clip_name}.jpg')

if __name__ == '__main__':
    main(*sys.argv[1:4])

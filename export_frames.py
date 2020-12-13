#!/usr/bin/env python3

import csv
import os
import sys

from turnovertools import sourcedb

def main(inputfile, table, db, outputdir):
    if isinstance(db, str):
        db = sourcedb.SourceTable(
            sourcedb.connect(database=db), table=table,
            keyfield='PrimaryKey')
        
    with open(inputfile, newline='') as csvfile:
        reader = csv.reader(csvfile)
        records = list(reader)

    for i, key in enumerate(row[0] for row in records):
        record = db[key]
        if record is None:
            print(f'No record found for {key}')
            continue
        reel = db[key]['reel']
        image = db.get_blob(key, 'image', 'JPEG')
        outname = f'{i:03}_{reel}.jpg'
        with open(os.path.join(outputdir, outname), 'wb') as outfile:
            outfile.write(image)

if __name__ == '__main__':
    main(*sys.argv[1:])

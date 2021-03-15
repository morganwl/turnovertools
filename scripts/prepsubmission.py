import csv
import os
import sys

from turnovertools.mediaobjects import MediaFile

def read_csv(inputfile):
    rows = list()
    with open(inputfile, newline='') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    return rows

def write_csv(rows, outputfile):
    with open(outputfile, 'wt') as fh:
        writer = csv.DictWriter(fh, rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def main(inputfile):
    base_dir = os.path.dirname(inputfile)
    rows = read_csv(inputfile)
    for row in rows:
        print(row['Filename'])
        if row['Filename'].endswith('.mov'):
            clip = MediaFile.probe(os.path.join(base_dir, row['Filename']))
            row['src_start_tc'] = clip.src_start_tc
            row['src_end_tc'] = clip.src_end_tc
    outputfile = inputfile.replace('.csv', '-1.csv')
    write_csv(rows, inputfile)

if __name__ == '__main__':
    main(sys.argv[1])

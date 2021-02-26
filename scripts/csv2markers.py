import csv
import sys

def main(marker_file):
    markers = list()
    with open(marker_file, newline='') as fh:
        reader = csv.reader(fh)
        last_marker = ('', '')
        for row in reader:
            marker = (row[0], row[1], f'V{row[2]}', row[3], row[4], '1')
            if last_marker != (row[1], row[2]):
                markers.append('\t'.join(marker))
            last_marker = (row[1], row[2])
    with open(marker_file, 'w') as fh:
        for marker in markers:
            fh.write(marker + '\n')

if __name__ == '__main__':
    main(sys.argv[1])

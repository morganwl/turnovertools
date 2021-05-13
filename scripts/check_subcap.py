import sys

def main(inputfile):
    with open(inputfile, encoding='mac-roman') as fh:
        last_out = None
        for line in fh:
            if line.count(':') == 6:
                timecodes = line.split(' ')
                if len(timecodes) == 2:
                    if last_out is not None and last_out > timecodes[0]:
                        print(f'Found error: {line}')
                    last_out = timecodes[1].rstrip()

if __name__ == '__main__':
    main(sys.argv[1])

#!/usr/bin/env python
# encoding=utf-8

from __future__ import print_function

import sys, re, os, json

if sys.version_info.major < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

def usage():
    print('Remove sentences from AMR', file=sys.stderr)
    print(file=sys.stderr)
    print('usage:', sys.argv[0], '<one-based sentence numbers to remove separated by single space>', '[one or more AMR files...]', file=sys.stderr)
    print(file=sys.stderr)

if __name__ == "__main__":

    args = sys.argv[1:]

    if '--help' in args or '-h' in args:
        usage()
        sys.exit(0)

    if len(args) < 1:
        usage()
        sys.exit(1)

    try:
        nrs = [int(x) for x in args.pop(0).split(' ') if x]
    except ValueError:
        print('error: invalid number list format', file=sys.stderr)
        sys.exit(1)

    for filename in args:
        if not os.path.isfile(filename):
            print('error: file not found:', filename)
            sys.exit(1)

    def sources():
        if args:
            for arg in args:
                with open(arg, 'rb') as f:
                    yield (line.decode('utf8', errors='replace') for line in f)
        else:
            usage()
            print('waiting for input from stdin', file=sys.stderr)
            yield sys.stdin

    try:

        def add(amr):
            global amrs
            # comment with at least :: and possibly AMR graph
            valid = False
            for line in amr:
                # if not line.startswith('#') or line.find('::') != -1:
                if not line.startswith('#'):
                    valid = True
                    break
            if valid:
                amrs.append(amr)

        amrs = []
        amr = []

        print('Loading...', file=sys.stderr)

        last = ''
        for f in sources():
            for line in f:
                line = line.rstrip()
                if line:
                    if line[0] == '#':
                        if amr and amr[-1][0] != '#':
                            add(amr)
                            amr = []
                    amr.append(line)
                else:
                    if amr:
                        add(amr)
                        amr = []
        if amr:
            add(amr)
            amr = []

        print(len(amrs), 'sentences found', file=sys.stderr)


        print('Removing...', file=sys.stderr)
        for nr in sorted(nrs, reverse=True):
            amr = amrs.pop(nr-1)
            print(nr, end=' ', file=sys.stderr)
            sys.stderr.flush()
        print('done', file=sys.stderr)


        print('Output resulting AMR', file=sys.stderr)
        for amr in amrs:
            for line in amr:
                print(line)
            print()

    except KeyboardInterrupt:
        print('Interrupted', file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python

import argparse
import os.path
import re
import shutil
import sys


PATTERN = re.compile(r'Error converting (?P<path>.*) to TIFF:')

def main ():
    parser = argparse.ArgumentParser(description='Copies unconverted images')
    parser.add_argument('log_file', type=argparse.FileType('rU'),
                        help='path to imgtojp2 log file')
    parser.add_argument('src_dir', help='path to unconverted images directory')
    parser.add_argument('dst_dir', help='path to converted images directory')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Provide verbose output')
    args = parser.parse_args()
    src_dir = os.path.abspath(args.src_dir)
    dst_dir = os.path.abspath(args.dst_dir)
    if not os.path.exists(args.dst_dir):
        sys.exit('Directory containing converted images must exist')
    for line in args.log_file:
        if not line.startswith('ERROR:'):
            continue
        match = PATTERN.search(line)
        if match:
            src = os.path.abspath(match.group('path'))
            move_image(src, src_dir, dst_dir, args.verbose)
        elif args.verbose:
            print('Skipping log line: %s' % line)

def move_image (src, src_dir, dst_dir, verbose):
    relpath = os.path.relpath(src, src_dir)
    dst = os.path.join(dst_dir, relpath)
    full_dst_dir = os.path.dirname(dst)
    if not os.path.exists(full_dst_dir):
        os.makedirs(full_dst_dir)
    if verbose:
        print('Copying "%s" to "%s"' % (src, dst))
    shutil.copy2(src, dst)


if __name__ == '__main__':
    main()

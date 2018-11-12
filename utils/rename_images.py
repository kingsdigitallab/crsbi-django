#!/usr/bin/env python

"""Script to rename a directory of images (possibly with
subdirectories) into JPEG 2000 images with regularised, non-meaningful
names. Also outputs a CSV mapping file that specifies the mapping
between the old and new filenames, and some image metadata."""

import argparse
import csv
import logging
import os
import os.path
import uuid

from common import get_normalised_name


class ImageConverter (object):

    def __init__ (self, in_dir, out_dir, map_file):
        self._in = os.path.abspath(in_dir)
        self._out = os.path.abspath(out_dir)
        self._map = os.path.abspath(map_file)
        self._mapping = {}

    def convert (self, force):
        try:
            os.mkdir(self._out)
        except OSError:
            if not force:
                raise
        self._get_original_metadata()
        self._rename()
        self._write_mapping()

    def _get_original_metadata (self):
        for root, dirs, files in os.walk(self._in):
            for name in files:
                path = os.path.join(root, name)
                rel_path = os.path.relpath(path, self._in)
                normalised_name = get_normalised_name(path)
                self._mapping[rel_path] = {
                    'normalised_name': normalised_name,
                    'old_name': name,
                    'old_path': rel_path}

    def _rename (self):
        # Rename the JPEG 2000 images. Note that this renames only
        # those images for which there is metadata in self._mapping;
        # there may be images that the JP2Converter converts that
        # imghdr did not recognise.
        for path in self._mapping:
            self._rename_file(path)

    def _rename_file (self, rel_path):
        old_path = os.path.join(self._in, rel_path)
        new_name = str(uuid.uuid4())
        directory = new_name[0]
        new_path = os.path.join(self._out, directory, new_name) + '.jp2'
        try:
            os.renames(old_path, new_path)
        except OSError:
            # If the rename fails, then set the entry to None
            # (removing it causes an error due to the dictionary's
            # size changing during iteration).
            self._mapping[rel_path] = None
        else:
            self._mapping[rel_path]['new_path'] = os.path.relpath(
                new_path, self._out)

    def reverse (self):
        fieldnames = ['normalised_name', 'old_name', 'old_path', 'new_path']
        reader = csv.DictReader(open(self._map, 'rb'), fieldnames=fieldnames)
        for row in reader:
            src = os.path.join(self._out, row['new_path'])
            dst = os.path.join(self._in, row['old_path'])
            os.renames(src, dst)

    def _write_mapping (self):
        # Write out the mapping to the map file.
        map_writer = csv.writer(open(self._map, 'wb'))
        for data in self._mapping.values():
            # A value of None indicates that the image was not
            # successfully converted to a JPEG 2000.
            if data is not None:
                data_list = [data['normalised_name'], data['old_name'],
                             data['old_path'], data['new_path']]
                map_writer.writerow(data_list)


def main ():
    parser = argparse.ArgumentParser(description='Convert images')
    parser.add_argument('in_dir', help='input directory of images',
                        metavar='IN')
    parser.add_argument('out_dir', help='output directory of images',
                        metavar='OUT')
    parser.add_argument('map', help='output mapping file', metavar='MAP')
    parser.add_argument('-f', '--force', action='store_true',
                        help='use an existing output directory')
    parser.add_argument('-r', '--reverse', action='store_true',
                        help='reverse the renaming')
    args = parser.parse_args()
    in_dir = args.in_dir
    out_dir = args.out_dir
    if args.reverse:
        if not os.path.exists(out_dir):
            parser.exit(status=1, message='output directory must exist\n')
    else:
        if not os.path.exists(in_dir):
            parser.exit(status=1, message='input directory must exist\n')
        if not args.force and os.path.lexists(out_dir):
            parser.exit(status=1, message='output directory must not exist\n')
    converter = ImageConverter(in_dir, out_dir, args.map)
    if args.reverse:
        converter.reverse()
    else:
        converter.convert(args.force)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        level=logging.WARN)
    main()

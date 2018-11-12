#!/usr/bin/env python

"""Script to detect sets of duplicate files within a directory and
copy the preferred file within each set into an output directory.

Duplicates are those files that have the same normalised name. The
duplicate that is copied is determined as follows:

 * If there is a version in the "web" subdirectory, that is used.

 * Otherwise, a randomly chosen file from the set of those with the
   highest file size is used.

"""

import argparse
import os
import shutil
import sys

from common import get_normalised_name


class DuplicateHandler (object):

    def __init__ (self):
        self._files_data = {}

    def _get_movable_duplicates (self, duplicates):
        """Returns a list of duplicates within `duplicates` that
        should be moved.

        That is, `duplicates` is returned without the single member
        that should not be moved.

        """
        duplicates.sort(key=lambda x: x['size'])
        return duplicates[:-1]

    def _copy_preferred (self, directory, preferred):
        dst = os.path.join(directory, preferred['rel_path'])
        try:
            os.makedirs(os.path.dirname(dst))
        except OSError:
            pass
        shutil.copy2(preferred['full_path'], dst)

    def copy_preferred (self, directory):
        """Copies the preferred file from each set of duplicates into
        `directory`."""
        directory = os.path.abspath(directory)
        for normalised_name, file_list in self._files_data.items():
            preferred = self._select_preferred(file_list)
            self._copy_preferred(directory, preferred)

    def scan (self, directory):
        """Scans `directory`, collecting information for duplicate
        detection."""
        directory = os.path.abspath(directory)
        self._files_data = {}
        for root, dirs, files in os.walk(directory):
            for name in files:
                if os.path.splitext(name)[1] != '.jp2':
                    continue
                full_path = os.path.abspath(os.path.join(root, name))
                dir_rel_path = os.path.relpath(root, directory)
                file_rel_path = os.path.relpath(full_path, directory)
                is_web = os.path.basename(dir_rel_path) == 'web'
                norm_name = get_normalised_name(name)
                stat = os.stat(full_path)
                file_data = {'full_path': full_path, 'mtime': stat.st_mtime,
                             'is_web': is_web, 'size': stat.st_size,
                             'rel_path': file_rel_path}
                self._files_data.setdefault(norm_name, []).append(file_data)

    def _select_preferred (self, file_list):
            if len(file_list) > 1:
                web = [duplicate for duplicate in file_list
                       if duplicate['is_web']]
                if web:
                    preferred = web[0]
                else:
                    file_list.sort(key=lambda x: x['size'])
                    preferred = file_list[-1]
            else:
                preferred = file_list[0]
            return preferred

def main ():
    parser = argparse.ArgumentParser(description='Detect duplicate files')
    parser.add_argument('in_dir', metavar='IN_DIR')
    parser.add_argument('out_dir', metavar='OUT_DIR')
    args = parser.parse_args()
    if not os.path.exists(args.in_dir):
        sys.exit('Directory containing potential duplicates must exist!')
    handler = DuplicateHandler()
    handler.scan(args.in_dir)
    handler.copy_preferred(args.out_dir)


if __name__ == '__main__':
    main()

import csv
import os.path
import sqlite3

import sculpture.management.migration_utils as migration_utils
import utils.common


def get_image_data (file_path, metadata_required):
    """Returns a dictionary of data for creating an image.

    Returns None if there was a problem.

    """
    lookup = ImageLookup()
    return lookup.lookup_by_filename(file_path, metadata_required=False)

def get_mapping ():
    mapping = {}
    field_names = ['normalised_name', 'old_name', 'old_path', 'new_path',
                   'image_type']
    reader = csv.DictReader(open(migration_utils.MAPPING_FILE, 'rb'),
                            fieldnames=field_names)
    for row in reader:
        mapping[row['normalised_name']] = row
    return mapping


class MissingImage (Exception):

    pass


class ImageLookup (object):

    """Class for lookup up the image path and metadata for the JPEG
    2000 image corresponding to `image_name`.

    This involves looking up `image_name` in the image metadata
    database and checking that it exists in archival JPEG 2000
    format.

    """

    mapping = get_mapping()
    conn = sqlite3.connect(migration_utils.DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    _c = conn.cursor()
    _c.execute('PRAGMA foreign_keys=ON')

    def _derive_file_format (self, filename):
        extension = os.path.splitext(filename)[1]
        file_format = ''
        if extension == '.jpg':
            file_format = 'JPEG'
        elif extension in ('.TIF', '.tif', '.id', '.if', '.tf', '.TIFF',
                           '.tiif'):
            file_format = 'TIFF'
        return file_format

    def _extract_metadata_from_map (self, original_image_base_name):
        image_map = self.mapping.get(original_image_base_name)
        if image_map is None:
            data = None
        else:
            data = {'image': image_map['new_path']}
        return data

    def _extract_metadata_from_row (self, row):
        upload_filename = row['output_file_name'] or ''
        upload_file_format = self._derive_file_format(upload_filename)
        data = {
            'caption': row['subject'],
            'bit_depth': row['output_colour_depth'] or '',
            'colour_mode': row['output_mode'] or '',
            'editing_software': row['image_processing_software'] or '',
            'resolution': row['scanning_resolution'],
            'upload_file_format': upload_file_format,
            'upload_filename': upload_filename,
            }
        try:
            data.update(self._extract_metadata_from_map(str(row['negative'])))
        except TypeError:
            data = None
        return data

    def lookup_by_filename (self, filename, metadata_required=True):
        """Returns a dictionary of image metadata for the image
        associated with `filename`."""
        image_base_name = utils.common.get_normalised_name(filename)
        # With 71 out of 24920 records in the database having the
        # Negative ID (in the negative field of Scanning) the same as
        # the non-extension part of output_file_name, and those 71
        # being always very close to the ID, it seems safe to assume
        # that those 71 are mistakes, and it is simplest to just
        # compare the Negative ID with the legacy_base_name.
        self._c.execute('''SELECT * FROM Scanning, Negative
                               WHERE Scanning.negative = ? AND
                                     Scanning.negative = Negative.id''',
                        (image_base_name,))
        rows = self._c.fetchall()
        data = None
        if len(rows) == 0:
            if metadata_required:
                print('Skipping image "%s"; no metadata' % filename)
            else:
                data = self._extract_metadata_from_map(image_base_name)
        elif len(rows) > 1:
            print('Skipping image "%s"; multiple matching metadata records' %
                  filename)
        else:
            data = self._extract_metadata_from_row(rows[0])
            if data is None:
                print('Skipping image "%s"; no matching image file' % filename)
            else:
                # Perform the more expensive author/photographer lookup.
                self._c.execute(
                    '''SELECT Person.forename, Person.surname
                           FROM Person, AuthorCounty, Location, Negative
                           WHERE Negative.id = ? AND
                                 Negative.location = Location.id AND
                                 Location.author_county = AuthorCounty.id AND
                                 AuthorCounty.person = Person.id''',
                    (image_base_name,))
                row = self._c.fetchone()
                if row is not None:
                    person_name = '%s %s' % (row['forename'], row['surname'])
                    photographer = migration_utils.get_or_create_contributor(
                        person_name)
                    data['photographer'] = photographer
        return data

    def lookup_by_location (self, location_id):
        """Returns a list of dictionaries of image metadata for the
        images associated with `location_id`, where `location_id` is
        an id from the Location table in the image metadata
        database."""
        data_list = []
        self._c.execute('''SELECT * FROM Negative, Scanning
                               WHERE Negative.location = ? AND
                                     Negative.publish_image_online = 1 AND
                                     Negative.id = Scanning.negative''',
                        (location_id,))
        for row in self._c.fetchall():
            data = self._extract_metadata_from_row(row)
            if data is None:
                print('Skipping image "%s"; no matching image file' %
                      row['negative'])
            else:
                data_list.append(data)
        return data_list

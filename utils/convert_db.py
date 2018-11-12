#!/usr/bin/env python3

"""Script for converting an MS Access image metadata database file
into a SQLite3 file.

Requires Python 3 due to problems I couldn't find an easy solution for
with CSV/Unicode/some detail I can't remember.

"""

import argparse
import csv
import os.path
import shlex
import sqlite3
import io
import subprocess
import sys


def main ():
    parser = argparse.ArgumentParser(
        description='Convert an Access metadata database to SQLite')
    parser.add_argument('mdb', metavar='ACCESS_DATABASE',
                        help='path to Access database file')
    parser.add_argument('db', metavar='SQLITE_DATABASE',
                        help='path to SQLite database file')
    args = parser.parse_args()
    if not os.path.exists(args.mdb):
        sys.exit('Access database must exist')
    if os.path.exists(args.db):
        sys.exit('SQLite database file already exists')
    create_db(args.db)
    convert_database(args.mdb, args.db)

def create_db (db_filename):
    """Creates the database and its schema."""
    conn = sqlite3.connect(os.path.abspath(db_filename))
    c = conn.cursor()
    c.execute('''CREATE TABLE Address (
                     id INTEGER PRIMARY KEY ASC,
                     first_name TEXT,
                     last_name TEXT
                 )''')
    c.execute('''CREATE TABLE AuthorCounty (
                     id INTEGER PRIMARY KEY ASC,
                     person INTEGER REFERENCES Person (id),
                     county INTEGER REFERENCES County (id)
                 )''')
    c.execute('''CREATE TABLE Committee (
                     person INTEGER REFERENCES Person (id),
                     surname TEXT,
                     forename TEXT,
                     title TEXT,
                     honours TEXT,
                     address_line_1 TEXT,
                     address_line_2 TEXT,
                     address_line_3 TEXT,
                     address_line_4 TEXT,
                     address_line_5 TEXT,
                     address_line_6 TEXT,
                     postcode TEXT,
                     home_telephone TEXT,
                     work_telephone TEXT,
                     fax TEXT,
                     email TEXT,
                     label TEXT,
                     salutation TEXT,
                     committee_member INTEGER NOT NULL,
                     author TEXT,
                     photographer TEXT,
                     editor TEXT,
                     geologist TEXT,
                     deceased TEXT,
                     other TEXT,
                     newsletter_only TEXT,
                     corpus_address_list INTEGER NOT NULL,
                     comments TEXT,
                     mailing_list INTEGER
                 )''')
    c.execute('''CREATE TABLE CostCode (
                     id INTEGER PRIMARY KEY ASC,
                     cost_code TEXT,
                     details TEXT
                 )''')
    c.execute('''CREATE TABLE Country (
                     abbreviation TEXT,
                     country TEXT
                 )''')
    c.execute('''CREATE TABLE County (
                     id INTEGER PRIMARY KEY ASC,
                     country TEXT,
                     county TEXT,
                     abbreviation TEXT
                 )''')
    c.execute('''CREATE TABLE Film (
                     film_number TEXT,
                     person INTEGER REFERENCES Person (id)
                 )''')
    c.execute('''CREATE TABLE LaunchList (
                     person INTEGER,
                     surname TEXT,
                     forename TEXT,
                     title TEXT,
                     honours TEXT,
                     both TEXT,
                     reception_only TEXT,
                     symposium_only TEXT,
                     no TEXT,
                     address_line_1 TEXT,
                     address_line_2 TEXT,
                     address_line_3 TEXT,
                     address_line_4 TEXT,
                     address_line_5 TEXT,
                     address_line_6 TEXT,
                     postcode TEXT,
                     home_telephone TEXT,
                     work_telephone TEXT,
                     fax TEXT,
                     email TEXT,
                     label TEXT,
                     salutation TEXT,
                     committee_member INTEGER NOT NULL,
                     author TEXT,
                     photographer TEXT,
                     editor TEXT,
                     geologist TEXT,
                     deceased TEXT,
                     other TEXT,
                     newsletter_only TEXT,
                     corpus_address_list INTEGER NOT NULL,
                     comments TEXT
                 )''')
    c.execute('''CREATE TABLE Location (
                     id INTEGER PRIMARY KEY ASC,
                     author_county INTEGER REFERENCES AuthorCounty,
                     type_of_building TEXT,
                     dedication_modern TEXT,
                     dedication_medieval TEXT,
                     diocese_modern TEXT,
                     diocese_medieval TEXT,
                     location TEXT,
                     file_name TEXT,
                     file_location TEXT,
                     online INTEGER NOT NULL,
                     date_site_visit TEXT,
                     date_received TEXT,
                     images_received INTEGER NOT NULL,
                     image_web_ready INTEGER NOT NULL,
                     comments TEXT
                 )''')
    c.execute('''CREATE TABLE Negative (
                     id INTEGER PRIMARY KEY ASC,
                     film_number TEXT,
                     location INTEGER REFERENCES Location (id),
                     frame_number TEXT,
                     cd_number INTEGER,
                     cd_frame_number INTEGER,
                     subject TEXT,
                     publish_image_online INTEGER NOT NULL,
                     placement_of_image_1 TEXT,
                     placement_of_image_2 TEXT,
                     sequence TEXT,
                     comments TEXT
                 )''')
    c.execute('''CREATE Table PasteError (
                     field TEXT
                 )''')
    c.execute('''CREATE TABLE Payment (
                     id INTEGER PRIMARY KEY ASC,
                     person INTEGER REFERENCES Person (id),
                     cost_code INTEGER REFERENCES CostCode (id),
                     date TEXT,
                     amount INTEGER,
                     total INTEGER
                 )''')
    c.execute('''CREATE TABLE Person (
                     id INTEGER PRIMARY KEY ASC,
                     surname TEXT,
                     forename TEXT,
                     title TEXT,
                     honours TEXT,
                     address_line_1 TEXT,
                     address_line_2 TEXT,
                     address_line_3 TEXT,
                     address_line_4 TEXT,
                     address_line_5 TEXT,
                     address_line_6 TEXT,
                     postcode TEXT,
                     home_telephone TEXT,
                     work_telephone TEXT,
                     fax TEXT,
                     email TEXT,
                     label TEXT,
                     salutation TEXT,
                     committee_memeber INTEGER NOT NULL,
                     author TEXT,
                     photographer TEXT,
                     editor TEXT,
                     geologist TEXT,
                     deceased TEXT,
                     other TEXT,
                     newsletter_only TEXT,
                     corpus_address_list INTEGER NOT NULL,
                     comments TEXT,
                     mailing_list INTEGER
                 )''')
    c.execute('''CREATE TABLE Scanning (
                     id INTEGER PRIMARY KEY ASC,
                     negative INTEGER REFERENCES Negative (id),
                     film_type_1 TEXT,
                     film_type_2 TEXT,
                     film_type_3 TEXT,
                     quality_of_original TEXT,
                     date_scanned TEXT,
                     person INTEGER REFERENCES Person (id),
                     scanner TEXT,
                     scanner_software TEXT,
                     image_processing_software TEXT,
                     scanning_resolution INTEGER,
                     input_height INTEGER,
                     input_width INTEGER,
                     input_file_size TEXT,
                     input_colour_depth TEXT,
                     input_mode TEXT,
                     input_cropping TEXT,
                     input_level_adjustment TEXT,
                     input_other_editing TEXT,
                     input_other_editing_2 TEXT,
                     output_resizing TEXT,
                     output_resolution INTEGER,
                     output_colour_depth TEXT,
                     output_mode TEXT,
                     output_width INTEGER,
                     output_height INTEGER,
                     output_file_size TEXT,
                     output_compression TEXT,
                     output_file_name TEXT,
                     comments TEXT,
                     cd_identity TEXT,
                     cd_2_identity TEXT
                 )''')
    conn.commit()
    c.close()

def convert_database (mdb_filename, db_filename):
    conn = sqlite3.connect(os.path.abspath(db_filename))
    c = conn.cursor()
    c.execute('PRAGMA foreign_keys=ON')
    convert_table(c, mdb_filename, 'Addresses', 'Address', 3)
    convert_table(c, mdb_filename, 'cost code table', 'CostCode', 3)
    convert_table(c, mdb_filename, 'country table', 'Country', 2)
    convert_table(c, mdb_filename, 'county table', 'County', 4)
    convert_table(c, mdb_filename, 'Paste Errors', 'PasteError', 1)
    convert_table(c, mdb_filename, 'person table', 'Person', 29)
    convert_table(c, mdb_filename, 'author/county link table', 'AuthorCounty',
                  3)
    convert_table(c, mdb_filename, 'committe table', 'Committee', 29)
    convert_table(c, mdb_filename, 'film table', 'Film', 2)
    convert_table(c, mdb_filename, 'launchlist', 'LaunchList', 32)
    convert_table(c, mdb_filename, 'location table', 'Location', 16)
    convert_table(c, mdb_filename, 'negative link table', 'Negative', 12)
    convert_table(c, mdb_filename, 'payments table', 'Payment', 6)
    convert_table(c, mdb_filename, 'scanning table', 'Scanning', 33)
    conn.commit()
    c.close()

def convert_table (c, mdb_filename, mdb_table, table, fields):
    data_reader = get_data_reader(mdb_filename, mdb_table)
    values = ', '.join(['?'] * fields)
    for row in data_reader:
        prepared_row = prepare_row(row)
        try:
            c.execute('''INSERT INTO %s VALUES (%s)''' % (table, values),
                      prepared_row)
        except sqlite3.IntegrityError:
            pass

def get_csv_data (mdb_filename, table_name):
    command = 'mdb-export -H %s "%s"' % (mdb_filename, table_name)
    data = subprocess.check_output(shlex.split(command))
    return io.StringIO(data.decode('utf-8'))

def get_data_reader (mdb_filename, table_name):
    csv_data = get_csv_data(mdb_filename, table_name)
    return csv.reader(csv_data, delimiter=',', quotechar='"')

def prepare_row (row):
    data = []
    for item in row:
        if not item:
            item = None
        else:
            try:
                item = int(item)
            except ValueError:
                pass
        data.append(item)
    return data


if __name__ == '__main__':
    main()

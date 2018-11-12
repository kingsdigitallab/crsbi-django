"""Common functions for the migration scripts."""

import os.path
import re

from django.contrib.auth.models import User
import django.utils.timezone

import sculpture.constants
import sculpture.models


DATABASE_FILE = os.path.abspath('legacy/image-metadata.db')
MAPPING_FILE = os.path.abspath('sculpture/management/image_map.csv')
NOW = django.utils.timezone.now()


def create_sort_text (text):
    text = text.strip(', ')
    if ',' in text:
        sort_text = text
    elif ' ' in text:
        pieces = text.split()
        sort_text = '%s, %s' % (pieces[-1], ' '.join(pieces[:len(pieces)-1]))
    else:
        sort_text = text
    if len(sort_text) > 32:
        sort_text = sort_text[:32]
    return sort_text

def get_or_create_contributor (name):
    try:
        contributor = sculpture.models.Contributor.objects.get(name=name)
    except sculpture.models.Contributor.DoesNotExist:
        user_profile = get_user_profile(name)
        contributor = sculpture.models.Contributor(
            name=name, user_profile=user_profile, created=NOW, modified=NOW)
        contributor.save()
    return contributor

def get_or_create_country (name):
    try:
        country = sculpture.models.Country.objects.get(name=name)
    except sculpture.models.Country.DoesNotExist:
        country = sculpture.models.Country(name=name, created=NOW, modified=NOW)
        country.save()
    return country

def get_or_create_dedication (name, created=NOW, modified=NOW):
    try:
        dedication = sculpture.models.Dedication.objects.get(name=name)
    except sculpture.models.Dedication.DoesNotExist:
        dedication = sculpture.models.Dedication(name=name, created=created,
                                                 modified=modified)
        dedication.save()
    return dedication

def get_or_create_diocese (name):
    try:
        diocese = sculpture.models.Diocese.objects.get(name=name)
    except sculpture.models.Diocese.DoesNotExist:
        diocese = sculpture.models.Diocese(name=name, created=NOW, modified=NOW)
        diocese.save()
    return diocese

def get_or_create_region (name, region_type):
    try:
        region = sculpture.models.Region.objects.get(
            name=name, region_type=region_type)
    except sculpture.models.Region.DoesNotExist:
        region = sculpture.models.Region(
            name=name, region_type=region_type, created=NOW, modified=NOW)
        region.save()
    return region

def get_or_create_settlement (name):
    try:
        settlement = sculpture.models.Settlement.objects.get(
            name__iexact=name)
    except sculpture.models.Settlement.DoesNotExist:
        settlement = sculpture.models.Settlement(name=name, created=NOW,
                                                 modified=NOW)
        settlement.save()
    return settlement

def get_user_profile (name):
    try:
        first_name, last_name = name.rsplit(None, 1)
    except ValueError:
        first_name, last_name = ('', name)
    try:
        user = User.objects.get(first_name=first_name, last_name=last_name)
        user_profile = user.get_profile()
    except User.DoesNotExist, User.MultipleObjectsReturned:
        user_profile = None
    return user_profile

def normalise_grid_reference (grid_reference):
    """Normalises `grid_reference`.

    The normalised form is sculpture.constants.GRID_PATTERN, which is
    suitable for both British National Grid and Irish National Grid
    coordinates.

    """
    if grid_reference == 'SV 855 936':
        grid_reference = 'SZ 855 936'
    if not grid_reference or re.match(sculpture.constants.GRID_PATTERN,
                                      grid_reference):
        return grid_reference
    grid_reference = grid_reference.replace('.', ' ')
    grid_reference = re.sub(r'\s+', ' ', grid_reference.strip(),
                            flags=re.UNICODE)
    if grid_reference.startswith('NGR '):
        grid_reference = grid_reference[4:]
    # Separate the tile reference (alphabetic) from the easting
    # (digits) with a space.
    grid_reference = re.sub(r'([A-Z])(\d)', r'\1 \2', grid_reference)
    # Remove everything preceding the first alphabetic character.
    grid_reference = re.sub(r'^[^A-Z]*([A-Z]+.*)$', r'\1', grid_reference)
    # Split a single cluster of digits into two equal length
    # groups, if possible.
    match = re.search(r'^(?P<prefix>[A-Z]{1,2}) (?P<digits>\d+)$',
                      grid_reference)
    if match:
        digits = match.group('digits')
        length = len(digits)
        if not length % 2:
            split = length / 2
            grid_reference = '%s %s %s' % \
                (match.group('prefix'), digits[:split], digits[split:])
    # Specific fixes for pathological cases.
    if grid_reference == 'SP SP 888 124':
        grid_reference = 'SP 888 124'
    elif grid_reference == 'SE 43 8 461':
        grid_reference = 'SE 438 461'
    elif grid_reference == 'TL 95 58 59':
        grid_reference = 'TL 955 859'
    elif grid_reference == 'S 0 839 527':
        grid_reference = 'SO 839 527'
    return grid_reference

def regularise_text (text):
    """Returns `text` in a regularised form.

    This consists of removing excess whitespace.

    """
    if not text:
        return ''
    return re.sub('\s\s+', ' ', text.strip())

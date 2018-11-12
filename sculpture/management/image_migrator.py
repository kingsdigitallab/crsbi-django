"""Module and class for creating new Sites from data held in the image
metadata database.

There are records in that database relating to a backlog of images
that have not been processed, but for which there are images and image
metadata. This migrator creates Site and Feature records to hold these
images, so that fieldworkers do not have to reupload images and
metadata.

"""

import re
import sqlite3

import django.db.utils

import sculpture.constants
import sculpture.management.image_lookup
import sculpture.management.migration_utils as migration_utils
import sculpture.management.migrator
import sculpture.models


class ImageMigrator (sculpture.management.migrator.Migrator):

    def __init__ (self):
        conn = sqlite3.connect(migration_utils.DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        self._c = conn.cursor()
        self._c.execute('PRAGMA foreign_keys=ON')
        self._draft_status = sculpture.models.SiteStatus.objects.get(
            name=sculpture.constants.SITE_STATUS_DRAFT)
        self._county_type = sculpture.models.RegionType.objects.get(
            name=sculpture.constants.REGION_TYPE_COUNTY)
        self._period_medieval = sculpture.models.Period.objects.get(
            name=sculpture.constants.DATE_MEDIEVAL)
        self._period_now = sculpture.models.Period.objects.get(
            name=sculpture.constants.DATE_NOW)
        self._map = {'contributor': {}, 'country': {}, 'county': {},
                     'dedication': {}, 'diocese': {}, 'settlement': {}}

    def _get_author_country_county (self, author_county_id):
        """Returns the Contributor, Country and County associated with
        `author_county_id`.

        The madness of this method is explained by the database
        structure that links Person and County together with Location.

        """
        if not author_county_id:
            return None, None, None
        self._c.execute('SELECT * FROM AuthorCounty WHERE id = ?',
                        (author_county_id,))
        row = self._c.fetchone()
        author = self._get_contributor_object(row['person'])
        country, county = self._get_country_county(row['county'])
        return author, country, county

    def _get_contributor_object (self, person_id):
        if not person_id:
            return None
        contributor = self._map['contributor'].get(person_id)
        if contributor is None:
            self._c.execute('SELECT forename, surname FROM Person WHERE id = ?',
                            (person_id,))
            row = self._c.fetchone()
            name = '%s %s' % (row['forename'], row['surname'])
            name = self._massage_contributor_name(name)
            contributor = migration_utils.get_or_create_contributor(name)
            self._map['contributor'][person_id] = contributor
        return contributor

    def _get_country_county (self, county_id):
        """Returns the Country and County objects associated with
        `county_id`."""
        if not county_id:
            return None, None
        self._c.execute('''SELECT County.county, Country.country
                               FROM County, Country
                               WHERE County.country = Country.abbreviation
                                   AND County.id = ?''', (county_id,))
        row = self._c.fetchone()
        country = self._get_country_object(row['country'])
        county = self._get_county_object(row['county'])
        return country, county

    def _get_country_object (self, name):
        country = self._map['country'].get(name)
        if country is None:
            country = migration_utils.get_or_create_country(name)
            self._map['country'][country] = country
        return country

    def _get_county_object (self, name):
        county = self._map['county'].get(name)
        if county is None:
            county = migration_utils.get_or_create_region(
                name, self._county_type)
            self._map['county'][name] = county
        return county

    def _get_dedication_object (self, name, period):
        name = self._massage_dedication_name(name, period)
        if not name:
            dedication = None
        else:
            dedication = self._map['dedication'].get(name)
            if dedication is None:
                dedication = migration_utils.get_or_create_dedication(name)
                self._map['dedication'][name] = dedication
        return dedication

    def _get_diocese_object (self, name, period):
        if not name:
            diocese = None
        else:
            name = self._massage_diocese_name(
                migration_utils.regularise_text(name), period)
            diocese = self._map['diocese'].get(name)
            if diocese is None:
                diocese = migration_utils.get_or_create_diocese(name)
                self._map['diocese'][name] = diocese
        return diocese

    def _get_settlement_object (self, name):
        if not name:
            settlement = None
        else:
            name = migration_utils.regularise_text(name)
            name = self._massage_settlement_name(name)
            settlement = self._map['settlement'].get(name)
            if settlement is None:
                settlement = migration_utils.get_or_create_settlement(name)
                self._map['settlement'][name] = settlement
        return settlement

    def _get_site_id (self, file_location):
        """Returns `file_location` in the format of a site_id."""
        if file_location is None:
            return None
        return file_location.replace('/', '-')

    def migrate (self):
        self._c.execute('SELECT * FROM Location')
        for row in self._c.fetchall():
            site_id = self._get_site_id(row['file_location'])
            if site_id and not sculpture.models.Site.objects.filter(
                site_id=site_id).count():
                self._migrate_site(row, site_id)

    def _migrate_dedication (self, site, dedication_text, period):
        data = self._split_dedication(dedication_text)
        for name, date, certain in data:
            dedication = self._get_dedication_object(name, period)
            if dedication:
                site_dedication = sculpture.models.SiteDedication(
                    site=site, dedication=dedication, period=period, date=date,
                    certain=certain)
                site_dedication.save()

    def _migrate_diocese (self, site, diocese_name, period):
        diocese = self._get_diocese_object(diocese_name, period)
        if diocese is not None:
            site_diocese = sculpture.models.SiteDiocese(
                site=site, diocese=diocese, period=period)
            site_diocese.save()

    def _migrate_images (self, site, location_id, author):
        lookup = sculpture.management.image_lookup.ImageLookup()
        for image_metadata in lookup.lookup_by_location(location_id):
            image_metadata['caption'] = image_metadata['caption'] or ''
            if author:
                image_metadata['photographer'] = author
            site_image = sculpture.models.SiteImage(site=site, **image_metadata)
            try:
                site_image.save()
            except django.db.utils.IntegrityError, e:
                print('Failed to save SiteImage: %s' % e)

    def _migrate_region (self, site, county):
        if county is not None:
            site_region = sculpture.models.SiteRegion(
                site=site, region=county, period=self._period_now)
            site_region.save()

    def _migrate_site (self, location_row, site_id):
        author, country, county = self._get_author_country_county(
            location_row['author_county'])
        if country is None:
            abbreviation = site_id[:2]
            if abbreviation == 'ed':
                country = self._get_country_object('England')
            elif abbreviation == 'id':
                country = self._get_country_object('Republic of Ireland')
            elif abbreviation == 'ni':
                country = self._get_country_object('Northern Ireland')
            elif abbreviation == 'sd':
                country = self._get_country_object('Scotland')
            elif abbreviation == 'ws':
                country = self._get_country_object('Wales')
            else:
                print('Skipping site "%s" due to missing country' % site_id)
                return
        settlement = self._get_settlement_object(
            location_row['type_of_building'])
        site = sculpture.models.Site(
            site_id=site_id,
            status=self._draft_status,
            visit_date='<p>%s</p>' % location_row['date_site_visit'],
            name=migration_utils.regularise_text(location_row['location']),
            country=country,
            settlement=settlement)
        site.save()
        if author:
            site.authors.add(author)
        self._migrate_region(site, county)
        self._migrate_dedication(site, location_row['dedication_modern'],
                                 self._period_now)
        self._migrate_dedication(site, location_row['dedication_medieval'],
                                 self._period_medieval)
        self._migrate_diocese(site, location_row['diocese_modern'],
                              self._period_now)
        self._migrate_diocese(site, location_row['diocese_medieval'],
                              self._period_medieval)
        self._migrate_images(site, location_row['id'], author)

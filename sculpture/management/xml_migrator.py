"""Module and class for migrating a Site defined in a legacy TEI XML
file."""

import os.path

from lxml import etree

import sculpture.constants
import sculpture.management.image_lookup
import sculpture.management.migration_utils as migration_utils
import sculpture.management.migrator
import sculpture.models


class XMLMigrator (sculpture.management.migrator.Migrator):

    def __init__ (self, filename, transform):
        self._filename = filename
        self._transform = transform
        self._site_id = os.path.splitext(os.path.basename(filename))[0]
        self._tree = None

    def _get_contributor (self, name):
        name = migration_utils.regularise_text(name)
        name = self._massage_contributor_name(name)
        return migration_utils.get_or_create_contributor(name)

    def _get_country (self, location):
        name = migration_utils.regularise_text(location.findtext('country'))
        name = self._massage_country_name(name)
        return migration_utils.get_or_create_country(name)

    def _get_dedication (self, name, period):
        """Returns the Dedication matching `name`.

        Creates a new Dedication if no existing Dedication matches.

        """
        name = self._massage_dedication_name(name, period)
        if name is None:
            return None
        return migration_utils.get_or_create_dedication(name)

    def _get_diocese (self, name, period):
        """Returns the Diocese matching `name`.

        Creates a new Diocese if no existing Diocese matches.

        """
        name = migration_utils.regularise_text(name)
        name = self._massage_diocese_name(name, period)
        if not name:
            return None
        return migration_utils.get_or_create_diocese(name)

    def _get_feature_set (self, feature):
        """Returns the FeatureSet for `feature`.

        Does not create a new FeatureSet if none is found.

        """
        try:
            xml_feature_set = feature.xpath('feature_set')[0]
        except IndexError:
            print('No feature set for feature in %s' % self._filename)
            raise
        name = migration_utils.regularise_text(xml_feature_set.findtext('name'))
        name = self._massage_feature_set_name(name)
        parent_name = migration_utils.regularise_text(
            xml_feature_set.findtext('feature_set/name'))
        parent_name = self._massage_feature_set_name(parent_name)
        if not parent_name:
            parent_name = None
        try:
            # There are *so many* case issues that doing a case
            # insensitive search is worth it.
            if not parent_name:
                feature_set = sculpture.models.FeatureSet.objects.get(
                    name__iexact=name, feature_set__isnull=True)
            else:
                feature_set = sculpture.models.FeatureSet.objects.get(
                    name__iexact=name, feature_set__name__iexact=parent_name)
        except sculpture.models.FeatureSet.DoesNotExist:
            if parent_name:
                return self._get_feature_set(xml_feature_set)
            print('%s: FeatureSet with name "%s" and parent "%s" does not exist'
                  % (self._filename, name, parent_name))
            raise
        return feature_set

    def _get_html (self, container):
        """Returns an HTML string of the content of `container`
        element."""
        if container is None:
            return ''
        text = []
        for element in container:
            text.append(etree.tostring(element, encoding='utf-8'))
        return '\n\n'.join(text)

    def _get_period (self, name):
        name = migration_utils.regularise_text(name).lower()
        name = self._massage_period_name(name)
        try:
            period = sculpture.models.Period.objects.get(name=name)
        except sculpture.models.Period.DoesNotExist:
            print('Period starting with %s does not exist' % name)
            period = None
        return period

    def _get_region (self, name):
        name = migration_utils.regularise_text(name)
        self._massage_region_name(name)
        if not name:
            return None
        region_type = sculpture.models.RegionType.objects.get(
            name=sculpture.constants.REGION_TYPE_COUNTY)
        return migration_utils.get_or_create_region(name, region_type)

    def _get_settlement (self, location):
        name = migration_utils.regularise_text(location.findtext('settlement'))
        name = name.rstrip('.')
        name = self._massage_settlement_name(name)
        return migration_utils.get_or_create_settlement(name)

    def _migrate_authors (self, site):
        for legacy_author in self._tree.xpath('/site/author'):
            author = self._get_contributor(legacy_author.text)
            site.authors.add(author)

    def _migrate_bibliography (self, site):
        for bibl in self._tree.xpath('/site/bibliography/bibl'):
            name = etree.tostring(bibl, encoding='utf-8')
            # name is wrapped in <bibl> </bibl>.
            start_index = name.find('>') + 1
            end_index = name.rfind('<')
            name = migration_utils.regularise_text(name[start_index:end_index])
            sort_text = bibl.text or ''
            if not len(bibl) and sort_text:
                sort_text = sort_text.split(',')[0]
            sort_under = migration_utils.create_sort_text(sort_text)
            if name:
                bibliography = sculpture.models.BibliographyItem(
                    site=site, name=name, sort_under=sort_under)
                bibliography.save()

    def _migrate_dedications (self, site, location):
        for legacy_dedication in location.xpath('dedications/dedication'):
            period = self._get_period(legacy_dedication.findtext('date'))
            if period is None:
                print('Skipping dedication for %s due to invalid date' %
                      self._filename)
                continue
            data = self._split_dedication(legacy_dedication.findtext('name'))
            for name, date, certain in data:
                dedication = self._get_dedication(name, period)
                if dedication is not None:
                    site_dedication = sculpture.models.SiteDedication(
                        site=site, dedication=dedication, period=period,
                        date=date, certain=certain)
                    site_dedication.save()

    def _migrate_details (self, legacy_feature, feature):
        for legacy_detail in legacy_feature.xpath('details/detail'):
            title = migration_utils.regularise_text(
                legacy_detail.findtext('name'))
            text = migration_utils.regularise_text(self._get_html(
                    legacy_detail.find('description')))
            detail = sculpture.models.Detail(
                feature=feature, title=title, text=text)
            detail.save()

    def _migrate_dimensions (self, legacy_feature, feature):
        for legacy_dimension in legacy_feature.xpath('dimensions/dimension'):
            dimension_type = migration_utils.regularise_text(
                legacy_dimension.findtext('type'))
            value = migration_utils.regularise_text(
                legacy_dimension.findtext('value'))
            section = migration_utils.regularise_text(
                legacy_dimension.findtext('section'))
            dimension = sculpture.models.Dimension(
                feature=feature, dimension_type=dimension_type,
                value=value, section=section)
            dimension.save()

    def _migrate_dioceses (self, site, location):
        for legacy_diocese in location.xpath('dioceses/diocese'):
            period = self._get_period(legacy_diocese.findtext('date'))
            if period is None:
                # QAZ: temporary to be able to move past problems this
                # script cannot fix.
                print('Skipping diocese for %s due to invalid date' %
                      self._filename)
                continue
            diocese = self._get_diocese(legacy_diocese.findtext('name'),
                                        period)
            if diocese is not None:
                site_diocese = sculpture.models.SiteDiocese(
                    site=site, diocese=diocese, period=period)
                site_diocese.save()

    def _migrate_features (self, site):
        xml_features = self._tree.xpath('/site/features/feature')
        db_features_count = 0
        for legacy_feature in xml_features:
            # QAZ: temporary to be able to move past problems this
            # script cannot fix.
            try:
                feature_set = self._get_feature_set(legacy_feature)
            except:
                continue
            name = migration_utils.regularise_text(
                legacy_feature.findtext('name'))
            description = self._get_html(legacy_feature.find('description'))
            feature = sculpture.models.Feature(
                site=site, feature_set=feature_set, name=name,
                description=description)
            feature.save()
            db_features_count += 1
            self._migrate_details(legacy_feature, feature)
            self._migrate_dimensions(legacy_feature, feature)
            self._migrate_feature_images(legacy_feature, feature)
        if db_features_count != len(xml_features):
            print('Feature migration for %s migrated %d of %d features' %
                  (self._filename, db_features_count, len(xml_features)))

    def _migrate_feature_images (self, legacy_feature, feature):
        for legacy_image in legacy_feature.xpath('images/image'):
            legacy_image_name = legacy_image.get('url')
            data = sculpture.management.image_lookup.get_image_data(
                legacy_image_name, False)
            if data is not None:
                data.update({
                    'caption': migration_utils.regularise_text(
                            legacy_image.text),
                    'feature': feature})
                feature_image = sculpture.models.FeatureImage(**data)
                feature_image.save()

    def _migrate_regions (self, site, location):
        for legacy_region in location.xpath('regions/region'):
            period = self._get_period(legacy_region.findtext('date'))
            region = self._get_region(legacy_region.findtext('name'))
            date = migration_utils.regularise_text(
                legacy_region.findtext('subdate'))
            if region is not None:
                site_region = sculpture.models.SiteRegion(
                    site=site, region=region, period=period, date=date)
                site_region.save()

    def _migrate_site (self):
        # All of the XML files are of published sites.
        status = sculpture.models.SiteStatus.objects.get(
            name=sculpture.constants.SITE_STATUS_PUBLISHED)
        location = self._tree.xpath('/site/location')[0]
        name = location.findtext('name')
        country = self._get_country(location)
        grid_reference = migration_utils.normalise_grid_reference(
            location.findtext('grid_reference'))
        settlement = self._get_settlement(location)
        site = sculpture.models.Site(
            site_id=self._site_id,
            status=status,
            name=name,
            country=country,
            grid_reference=grid_reference,
            settlement=settlement,
            description=self._get_html(self._tree.xpath('/site/description')),
            history=self._get_html(self._tree.xpath('/site/history')),
            comments=self._get_html(self._tree.xpath('/site/comments')))
        site.save()
        self._migrate_regions(site, location)
        self._migrate_dioceses(site, location)
        self._migrate_dedications(site, location)
        self._migrate_authors(site)
        self._migrate_site_images(site)
        self._migrate_features(site)
        self._migrate_bibliography(site)

    def _migrate_site_images (self, site):
        for legacy_image in self._tree.xpath('/site/images/image'):
            legacy_image_name = legacy_image.get('url')
            data = sculpture.management.image_lookup.get_image_data(
                legacy_image_name, False)
            if data is not None:
                data.update({
                    'caption': migration_utils.regularise_text(
                            legacy_image.text),
                    'site': site})
                site_image = sculpture.models.SiteImage(**data)
                site_image.save()

    def migrate (self):
        # First check that this file needs to be migrated (ie, that it
        # wasn't generated from the legacy Django data).
        try:
            sculpture.models.Site.objects.get(site_id=self._site_id)
        except sculpture.models.Site.DoesNotExist:
            self._tree = self._transform(etree.parse(self._filename))
            self._migrate_site()

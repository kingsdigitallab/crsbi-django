"""Module and class for migrating data from the legacy Django
database."""

import lxml.html
import lxml.html.clean

from django.contrib.auth.models import User

import legacy.models
import sculpture.management.image_lookup
import sculpture.management.migration_utils as migration_utils
import sculpture.management.migrator
import sculpture.models


class DBMigrator (sculpture.management.migrator.Migrator):

    def __init__ (self, id_map, now):
        self._id_map = id_map
        self._now = now

    def _get_dedication (self, name, legacy_dedication, period):
        name = self._massage_dedication_name(name, period)
        if name is None:
            return None
        return migration_utils.get_or_create_dedication(
            name, legacy_dedication.created, legacy_dedication.modified)

    def _get_feature_set_order (self, legacy_order):
        """Returns an integer suitable for automatic ordering based on
        `legacy_order'."""
        if legacy_order in ('III', 'a.', '1.'):
            order = 1
        elif legacy_order in ('IV', 'b.', '2.', '2. '):
            order = 2
        elif legacy_order in ('V', 'c.', '3.'):
            order = 3
        elif legacy_order in ('VI', 'd.', '4.'):
            order = 4
        elif legacy_order in ('5.',):
            order = 5
        else:
            order = None
        return order

    def _get_object (self, model, model_name, legacy_id):
        object_id = self._id_map[model_name][legacy_id]
        return model.objects.get(id=object_id)

    def _get_publication (self, legacy_bibliography, author):
        try:
            publication_info_id = legacy_bibliography.publication_info
        except AttributeError:
            publication_info_id = ''
        legacy_id = '%s_%s' % (legacy_bibliography.title.id,
                               publication_info_id)
        try:
            publication = self._get_object(
                sculpture.models.BibliographyPublication,
                'bibliography_publication', legacy_id)
        except KeyError:
            try:
                publication_info = migration_utils.regularise_text(
                    legacy_bibliography.publication_info.publication_info)
            except AttributeError:
                publication_info = ''
            publication = sculpture.models.BibliographyPublication(
                author=author, title=legacy_bibliography.title.title,
                publication_info=publication_info)
            self._migrate_timestamps(legacy_bibliography, publication)
            publication.save()
            self._id_map['bibliography_publication'][legacy_id] = publication.id
        return publication

    def _migrate_contributor (self, legacy_contributor):
        name = migration_utils.regularise_text(legacy_contributor.name)
        try:
            first_name, last_name = name.rsplit(None, 1)
        except ValueError:
            first_name, last_name = ('', name)
        try:
            user = User.objects.get(first_name=first_name,
                                    last_name=last_name)
            user_profile = sculpture.utils.get_profile(user)
        except User.DoesNotExist, User.MultipleObjectsReturned:
            user_profile = None
        contributor = sculpture.models.Contributor(name=name,
                                                   user_profile=user_profile)
        self._migrate_timestamps(legacy_contributor, contributor)
        contributor.save()
        return contributor

    def migrate (self):
        # Migrate models that have no foreign key or many to many
        # fields.
        self.migrate_contributor()
        self.migrate_country()
        self.migrate_period()
        self.migrate_region_type()
        self.migrate_settlement()
        self.migrate_status()
        # Migrate models that reference other models that do not
        # themselves reference other models. Note that dedications are
        # handled differently, since one legacy record may become
        # multiple new records.
        self.migrate_diocese()
        self.migrate_feature_set()
        self.migrate_region()
        # Migrate remaining models. The order is important.
        self.migrate_site()
        self.migrate_feature()
        self.migrate_detail()
        self.migrate_dimension()

    def migrate_bibliography (self, site, legacy_bibliography):
        texts = []
        author = legacy_bibliography.author
        sort_under = ''
        if author:
            author_text = self._trim_bibliography_text(str(author))
            texts.append(author_text)
            sort_under = migration_utils.create_sort_text(author_text)
        article_title = legacy_bibliography.article_title
        if article_title:
            texts.append(self._trim_bibliography_text(str(article_title)))
        texts.append('<i>%s</i>' % str(legacy_bibliography.title))
        if not sort_under:
            sort_under = migration_utils.create_sort_text(
                str(legacy_bibliography.title))
        if legacy_bibliography.publication_info:
            texts.append(self._trim_bibliography_text(
                    str(legacy_bibliography.publication_info)))
        if legacy_bibliography.pages:
            texts.append(self._trim_bibliography_text(
                    legacy_bibliography.pages))
        name = ', '.join(texts) + '.'
        item = sculpture.models.BibliographyItem(
            site=site, name=name, sort_under=sort_under, created=self._now,
            modified=self._now)
        item.save()

    def migrate_contributor (self):
        self._id_map['contributor'] = {}
        for legacy_author in legacy.models.Author.objects.all():
            contributor = self._migrate_contributor(legacy_author)
            legacy_id = 'a%d' % legacy_author.id
            self._id_map['contributor'][legacy_id] = contributor.id
        for legacy_photographer in legacy.models.Photographer.objects.all():
            # There is overlap between Authors and Photographers, so
            # reuse an existing Contributor record.
            try:
                contributor = sculpture.models.Contributor.objects.get(
                    name=migration_utils.regularise_text(
                        legacy_photographer.name))
            except sculpture.models.Contributor.DoesNotExist:
                contributor = self._migrate_contributor(legacy_photographer)
            legacy_id = 'p%d' % legacy_photographer.id
            self._id_map['contributor'][legacy_id] = contributor.id
        for legacy_site in legacy.models.SculptureSite.objects.all():
            user = legacy_site.author.user
            try:
                contributor = sculpture.utils.get_profile(user).contributor
            except sculpture.models.Contributor.DoesNotExist:
                if user.first_name or user.last_name:
                    name = '%s %s' % (user.first_name, user.last_name)
                else:
                    name = user.username
                contributor = sculpture.models.Contributor(
                    name=name, user_profile=sculpture.utils.get_profile(user),
                    created=self._now, modified=self._now)
                contributor.save()
            legacy_id = 'u%d' % user.id
            self._id_map['contributor'][legacy_id] = contributor.id

    def migrate_country (self):
        self._id_map['country'] = {}
        for legacy_country in legacy.models.Country.objects.all():
            country = sculpture.models.Country(name=legacy_country.name)
            self._migrate_timestamps(legacy_country, country)
            country.save()
            self._id_map['country'][legacy_country.id] = country.id

    def migrate_detail (self):
        self._id_map['detail'] = {}
        # QAZ: Restrict to those which are associated with Features
        # that are associated with a Site?
        for legacy_detail in legacy.models.Detail.objects.all():
            try:
                feature = self._get_object(sculpture.models.Feature,
                                           'feature', legacy_detail.feature.id)
            except KeyError:
                print('Skipping Detail associated with a skipped Feature')
                continue
            title = migration_utils.regularise_text(legacy_detail.title)
            text = self._tidy_html(legacy_detail.text)
            detail = sculpture.models.Detail(feature=feature, title=title,
                                             text=text)
            self._migrate_timestamps(legacy_detail, detail)
            detail.save()
            self._id_map['detail'][legacy_detail.id] = detail.id

    def migrate_dimension (self):
        self._id_map['dimension'] = {}
        # QAZ: Restrict to those which are associated with Features
        # that are associated with a Site?
        for legacy_dimension in legacy.models.Dimension.objects.all():
            try:
                feature = self._get_object(sculpture.models.Feature, 'feature',
                                           legacy_dimension.feature.id)
            except KeyError:
                print('Skipping Dimension associated with a skipped Feature')
                continue
            dimension_type = migration_utils.regularise_text(
                legacy_dimension.type)
            value = migration_utils.regularise_text(legacy_dimension.value)
            dimension = sculpture.models.Dimension(
                feature=feature, dimension_type=dimension_type, value=value)
            self._migrate_timestamps(legacy_dimension, dimension)
            dimension.save()
            self._id_map['dimension'][legacy_dimension.id] = dimension.id

    def migrate_diocese (self):
        self._id_map['diocese'] = {}
        for legacy_diocese in legacy.models.Diocese.objects.all():
            period = self._get_object(sculpture.models.Period, 'period',
                                      legacy_diocese.date.id)
            name = migration_utils.regularise_text(legacy_diocese.name)
            name = self._massage_diocese_name(name, period)
            try:
                diocese = sculpture.models.Diocese.objects.get(name=name)
            except sculpture.models.Diocese.DoesNotExist:
                diocese = sculpture.models.Diocese(name=name)
                self._migrate_timestamps(legacy_diocese, diocese)
                diocese.save()
            self._id_map['diocese'][legacy_diocese.id] = diocese.id

    def migrate_feature (self):
        self._id_map['feature'] = {}
        # QAZ: Restrict to those features associated with a Site?
        for legacy_feature in legacy.models.Feature.objects.all():
            feature_set = self._get_object(
                sculpture.models.FeatureSet, 'feature_set',
                legacy_feature.feature_set.id)
            try:
                site = self._get_object(sculpture.models.Site, 'site',
                                        legacy_feature.site.id)
            except AttributeError:
                print('Skipping Feature with no associated Site')
                continue
            name = migration_utils.regularise_text(legacy_feature.name)
            description = self._tidy_html(legacy_feature.description)
            feature = sculpture.models.Feature(
                site=site, feature_set=feature_set, name=name,
                description=description)
            self._migrate_timestamps(legacy_feature, feature)
            feature.save()
            self._id_map['feature'][legacy_feature.id] = feature.id
            for legacy_feature_image in legacy_feature.feature_images.all():
                self.migrate_feature_image(feature, legacy_feature_image)

    def migrate_feature_image (self, feature, legacy_feature_image):
        data = sculpture.management.image_lookup.get_image_data(
            legacy_feature_image.image.name, False)
        if data is not None:
            data.update({
                'caption': migration_utils.regularise_text(
                    legacy_feature_image.caption),
                'feature': feature})
            feature_image = sculpture.models.FeatureImage(**data)
            self._migrate_timestamps(legacy_feature_image, feature_image)
            feature_image.save()

    def migrate_feature_set (self):
        # Rather than do anything clever to handle the self-reference
        # on this model, just pass over them twice, adding the
        # references on the second round, since it is optional.
        self._id_map['feature_set'] = {}
        for legacy_feature_set in legacy.models.FeatureSet.objects.all():
            order = self._get_feature_set_order(legacy_feature_set.n)
            name = migration_utils.regularise_text(legacy_feature_set.name)
            name = self._massage_feature_set_name(name)
            n = migration_utils.regularise_text(legacy_feature_set.n).strip('.')
            feature_set = sculpture.models.FeatureSet(order=order, name=name,
                                                      n=n)
            self._migrate_timestamps(legacy_feature_set, feature_set)
            feature_set.save()
            self._id_map['feature_set'][legacy_feature_set.id] = feature_set.id
        for legacy_feature_set in legacy.models.FeatureSet.objects.all():
            if legacy_feature_set.feature_set is not None:
                feature_set = self._get_object(
                    sculpture.models.FeatureSet, 'feature_set',
                    legacy_feature_set.id)
                parent_feature_set = self._get_object(
                    sculpture.models.FeatureSet, 'feature_set',
                    legacy_feature_set.feature_set.id)
                feature_set.feature_set = parent_feature_set
                self._migrate_timestamps(legacy_feature_set, feature_set)
                feature_set.save()

    def migrate_period (self):
        self._id_map['period'] = {}
        for legacy_period in legacy.models.DateType.objects.all():
            name = migration_utils.regularise_text(legacy_period.name)
            period = sculpture.models.Period(name=name)
            self._migrate_timestamps(legacy_period, period)
            period.save()
            self._id_map['period'][legacy_period.id] = period.id

    def migrate_region (self):
        self._id_map['region'] = {}
        for legacy_region in legacy.models.Region.objects.all():
            region_type = self._get_object(sculpture.models.RegionType,
                                           'region_type', legacy_region.type.id)
            name = migration_utils.regularise_text(legacy_region.name)
            try:
                region = sculpture.models.Region.objects.get(
                    name=name, region_type=region_type)
            except sculpture.models.Region.DoesNotExist:
                region = sculpture.models.Region(
                    name=name, region_type=region_type)
                self._migrate_timestamps(legacy_region, region)
                region.save()
            self._id_map['region'][legacy_region.id] = region.id

    def migrate_region_type (self):
        self._id_map['region_type'] = {}
        for legacy_region_type in legacy.models.RegionType.objects.all():
            name = migration_utils.regularise_text(legacy_region_type.name)
            region_type = sculpture.models.RegionType(name=name)
            self._migrate_timestamps(legacy_region_type, region_type)
            region_type.save()
            self._id_map['region_type'][legacy_region_type.id] = region_type.id

    def migrate_settlement (self):
        self._id_map['settlement'] = {}
        for legacy_settlement in legacy.models.Settlement.objects.all():
            name = migration_utils.regularise_text(legacy_settlement.name)
            name = self._massage_settlement_name(name)
            try:
                settlement = sculpture.models.Settlement.objects.get(name=name)
            except sculpture.models.Settlement.DoesNotExist:
                settlement = sculpture.models.Settlement(name=name)
                self._migrate_timestamps(legacy_settlement, settlement)
                settlement.save()
            self._id_map['settlement'][legacy_settlement.id] = settlement.id

    def migrate_site (self):
        # QAZ: Finish this: author, photographers, associated_sites...
        self._id_map['site'] = {}
        for legacy_site in legacy.models.SculptureSite.objects.all():
            country = self._get_object(sculpture.models.Country, 'country',
                                       legacy_site.country.id)
            try:
                settlement = self._get_object(
                    sculpture.models.Settlement, 'settlement',
                    legacy_site.settlement.id)
            except AttributeError:
                settlement = None
            status = self._get_object(sculpture.models.SiteStatus,
                                      'site_status', legacy_site.status.id)
            site = sculpture.models.Site(
                site_id=legacy_site.site_id,
                status=status,
                visit_date=self._tidy_html(legacy_site.visit_date),
                name=migration_utils.regularise_text(legacy_site.name),
                country=country,
                grid_reference=migration_utils.normalise_grid_reference(
                    legacy_site.key),
                settlement=settlement,
                description=self._tidy_html(legacy_site.description),
                history=self._tidy_html(legacy_site.history),
                comments=self._tidy_html(legacy_site.comments))
            self._migrate_timestamps(legacy_site, site)
            site.save()
            for legacy_author in legacy_site.authors.all():
                author = self._get_object(
                    sculpture.models.Contributor, 'contributor',
                    'a%d' % legacy_author.id)
                site.authors.add(author)
            # Add the record author to the list of authors; that
            # distinction has been removed.
            author = self._get_object(
                sculpture.models.Contributor, 'contributor',
                'u%d' % legacy_site.author.user.id)
            site.authors.add(author)
            for legacy_bibliography in legacy_site.bibliographies.all():
                self.migrate_bibliography(site, legacy_bibliography)
            for legacy_dedication in legacy_site.dedications.all():
                self.migrate_site_dedication(site, legacy_dedication)
            for legacy_diocese in legacy_site.dioceses.all():
                self.migrate_site_diocese(site, legacy_diocese)
            for legacy_region in legacy_site.regions.all():
                self.migrate_site_region(site, legacy_region)
            for legacy_site_image in legacy_site.site_images.all():
                self.migrate_site_image(site, legacy_site_image)
            self._id_map['site'][legacy_site.id] = site.id

    def migrate_site_dedication (self, site, legacy_dedication):
        period = self._get_object(sculpture.models.Period, 'period',
                                  legacy_dedication.date.id)
        data = self._split_dedication(legacy_dedication.name)
        for name, date, certain in data:
            dedication = self._get_dedication(name, legacy_dedication, period)
            if dedication is not None:
                site_dedication = sculpture.models.SiteDedication(
                    site=site, dedication=dedication, period=period, date=date,
                    created=self._now, modified=self._now)
                site_dedication.save()

    def migrate_site_diocese (self, site, legacy_diocese):
        period = self._get_object(sculpture.models.Period, 'period',
                                  legacy_diocese.date.id)
        diocese = self._get_object(sculpture.models.Diocese, 'diocese',
                                   legacy_diocese.id)
        site_diocese = sculpture.models.SiteDiocese(
            site=site, diocese=diocese, period=period,
            created=self._now, modified=self._now)
        site_diocese.save()

    def migrate_site_image (self, site, legacy_site_image):
        data = sculpture.management.image_lookup.get_image_data(
            legacy_site_image.image.name, False)
        if data is not None:
            data.update({
                'caption': migration_utils.regularise_text(
                    legacy_site_image.caption),
                'site': site})
            site_image = sculpture.models.SiteImage(**data)
            self._migrate_timestamps(legacy_site_image, site_image)
            site_image.save()

    def migrate_site_region (self, site, legacy_region):
        period = self._get_object(sculpture.models.Period, 'period',
                                  legacy_region.date.id)
        region = self._get_object(sculpture.models.Region, 'region',
                                  legacy_region.id)
        site_region = sculpture.models.SiteRegion(
            site=site, region=region, period=period, created=self._now,
            modified=self._now)
        site_region.save()

    def migrate_status (self):
        self._id_map['site_status'] = {}
        for legacy_status in legacy.models.Status.objects.all():
            status = sculpture.models.SiteStatus(name=legacy_status.name)
            self._migrate_timestamps(legacy_status, status)
            status.save()
            self._id_map['site_status'][legacy_status.id] = status.id

    def _migrate_timestamps (self, legacy_object, current_object):
        current_object.created = legacy_object.created
        current_object.modified = legacy_object.modified

    def _tidy_html (self, text):
        """Returns `text` with entity references removed or decoded
        and multiple spaces collapsed."""
        if not text:
            return ''
        text = text.replace('&nbsp;', ' ')
        cleaner = lxml.html.clean.Cleaner(remove_tags=('a',))
        text = cleaner.clean_html(text)
        html = lxml.html.fragment_fromstring(text, create_parent='div')
        # Remove the added enclosing div.
        text = lxml.html.tostring(html, encoding='utf-8')[5:-6]
        return migration_utils.regularise_text(text)

    def _trim_bibliography_text (self, text):
        text = text.strip('., \t\r\n')
        return text

import re

import pyproj

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from collections import OrderedDict as SortedDict

import mezzanine.core.fields
import mezzanine.pages

import sculpture.constants
import sculpture.utils
from .base_model import BaseModel
from .contributor import Contributor
from .country import Country
from .dedication import Dedication
from .diocese import Diocese
from .glossary_term import GlossaryTerm
from .period import Period
from .region import Region
from .settlement import Settlement


class PublishedSiteManager (models.GeoManager):

    def filter_by_feature_set (self, feature_set_id):
        return self.filter(features__feature_set=feature_set_id).distinct()

    def get_query_set (self):
        published_statuses = [
            sculpture.constants.SITE_STATUS_PUBLISHED,
            sculpture.constants.SITE_STATUS_PUBLISHED_INCOMPLETE]

        return super(PublishedSiteManager, self).get_query_set().filter(
            status__name__in=published_statuses)


class Site (BaseModel):

    # Formerly the SculptureSite model.

    # QAZ: How, when, by whom and why are site_ids assigned?
    site_id = models.CharField(max_length=16, blank=True)
    status = models.ForeignKey('SiteStatus')
    visit_date = models.CharField(
        max_length=216, blank=True, help_text='Eg: 01 Jan 2013',
        verbose_name='visit date(s)')
    authors = models.ManyToManyField(Contributor, blank=True,
                                     related_name='sites')
    fieldworker_may_2017 = models.CharField(
        max_length=2048, blank=True, help_text="Fieldworkers as of May 2018", 
        verbose_name="May 2018 Fieldworkers") # I know 2017 != 2018
    name = models.CharField(max_length=256)
    country = models.ForeignKey(Country)
    grid_reference = models.CharField(
        'national grid reference', max_length=25, blank=True,
        help_text='E.g. SO 123 321 or N 31 22')
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    location = models.PointField(blank=True, null=True)
    regions = models.ManyToManyField(Region, blank=True,
                                     related_name='sites', through='SiteRegion')
    dioceses = models.ManyToManyField(
        Diocese, blank=True, related_name='sites',
        through='SiteDiocese')
    dedications = models.ManyToManyField(
        Dedication, blank=True, related_name='sites',
        through='SiteDedication')
    settlement = models.ForeignKey(Settlement, blank=True, null=True,
                                   help_text='Type of building/monument',
                                   related_name='sites')
    description = mezzanine.core.fields.RichTextField(blank=True)
    history = mezzanine.core.fields.RichTextField(blank=True)
    comments = mezzanine.core.fields.RichTextField(blank=True)
    fieldworker_notes = models.TextField(
        blank=True, help_text='Admin use only; not published. Please add date and initials to all comments.')
    editor_notes = models.TextField(blank=True,
                                    help_text='Admin use only; not published. Please add date and initials to all comments.')
    glossary_terms = models.ManyToManyField(
        GlossaryTerm, blank=True, editable=False,
        related_name='sites')

    objects = models.GeoManager()
    published = PublishedSiteManager()

    bng_proj = pyproj.Proj(init='epsg:27700')
    ing_proj = pyproj.Proj(init='epsg:29901')
    geo_proj = pyproj.Proj(init='epsg:4326')

    title = models.CharField(blank=True, null=True, max_length=256)

    class Meta:
        app_label = 'sculpture'
        ordering = ['name']

    def __str__ (self):
        return self.name

    def _convert_refs (self):
        for field in ('description', 'history', 'comments'):
            content = sculpture.utils.convert_refs_to_links(
                getattr(self, field))
            setattr(self, field, content)

    def _derive_gis_data (self):
        """Sets latitude, longitude and point fields, derived from
        grid_reference field value."""
        result = re.search(sculpture.constants.GRID_PATTERN,
                           self.grid_reference)
        if result is not None:
            if result.group('bng'):
                proj = self.bng_proj
                grid_group = 2
                easting_group = 3
                northing_group = 4
            else:
                proj = self.ing_proj
                grid_group = 6
                easting_group = 7
                northing_group = 8
            easting, northing = self._expand_grid_reference(
                result.group(grid_group), result.group(easting_group),
                result.group(northing_group))
            longitude, latitude = pyproj.transform(proj, self.geo_proj, easting,
                                                   northing)
            self.location = Point(longitude, latitude, srid=4326)
            self.latitude = latitude
            self.longitude = longitude

    def _expand_grid_reference (self, grid, easting, northing):
        """Returns full easting and northing values (in metres) by
        joining `easting` and `northing` to `grid`.

        :param grid: BNG or ING grid label
        :type grid: `str`
        :param easting: easting value relative to `grid`
        :type easting: `str`
        :param northing: northing value relative to `grid`
        :type northing: `str`
        :rtype: `tuple` of `int`

        """
        base = sculpture.constants.NG_TILES.get(grid, '')
        # easting and northing may be a variable number of digits, so
        # convert them to the appropriate number of metres. 23 =
        # 23000m, 234 = 23400m, etc.
        easting = int(easting) * 10**(5 - len(easting))
        northing = int(northing) * 10**(5 - len(northing))
        # Each grid is 100km x 100km.
        full_easting = base[0] * 100000 + easting
        full_northing = base[1] * 100000 + northing
        return full_easting, full_northing

    def feature_sets (self):
        """Returns the FeatureSets that are related to this Site.

        Used to generate search facets, since relations of relations
        are not handled by Haystack, apparently.

        """
        from .feature_set import FeatureSet
        return FeatureSet.objects.filter_by_site(self.id)

    @models.permalink
    def get_absolute_url (self):
        return ('site_display', (), {'site_id': str(self.id)})

    def get_dedication_by_period (self, period_name):
        """Returns this site's dedications for the period
        `period_name`.

        :rtype: `QuerySet`

        """
        try:
            period = Period.objects.get(name=period_name)
        except Period.DoesNotExist:
            return Dedication.objects.none()
        return self.sitededication_set.filter(period=period)

    def get_dedication_now (self):
        """Returns this site's dedications associated with the period
        "now".

        :rtype: `QuerySet`

        """
        return self.get_dedication_by_period(sculpture.constants.DATE_NOW)


    def get_dedications (self):
        """Returns this site's dedications for all periods, grouped by
        period.

        :rtype: `dict`

        """
        dedications = {}
        for period in (sculpture.constants.DATE_MEDIEVAL,
                       sculpture.constants.DATE_NOW):
            dedications[period] = self.get_dedication_by_period(period)
        return dedications

    def get_features (self):
        """Returns this site's features organised into nested
        SortedDicts by feature set."""
        features = SortedDict()
        features['features'] = []
        # Iterate over Features, which are in the desired final order,
        # and group them according to the FeatureSet hierarchy. This
        # grouping removes duplication (ie, each FeatureSet will occur
        # only once), which may change the specified order. The first
        # occurrence of a FeatureSet determines its placement in the
        # order.
        for feature in self.features.all():
            fs_rank = features
            feature_sets = feature.get_feature_set_hierarchy()
            i = 1
            for feature_set in feature_sets:
                container = SortedDict()
                fs_rank = fs_rank.setdefault(feature_set, container)
                if 'features' not in fs_rank:
                    fs_rank['features'] = []
                i += 1
            fs_rank['features'].append(feature)
        return features

    def get_images (self):
        from .feature_image import FeatureImage
        return list(self.images.all()) + list(FeatureImage.objects.filter(
            feature__site=self))


    def get_images_features_first(self):
        from .feature_image import FeatureImage
        return list(FeatureImage.objects.filter(feature__site=self)) + list(self.images.all())


    def get_region_by_period (self, period_name):
        """Returns this site's regions of period `period_name`.

        :param period_name: name of period
        :type period_name: `str`
        :rtype: `QuerySet`

        """
        try:
            period = Period.objects.get(name=period_name)
        except Period.DoesNotExist:
            return Region.objects.none()
        return self.siteregion_set.filter(period=period)

    def get_region_traditional (self):
        """Returns this site's regions associated with the "traditional"
        period.

        :rtype: `QuerySet`

        """
        counties = self.get_region_by_period(
            sculpture.constants.DATE_TRADITIONAL)
        return counties

    def get_tags (self, user):
        """Returns a QuerySet of SiteTags associated with this site
        and belonging to `user`.

        :param user: user profile
        :type user: `UserProfile`

        """
        return self.tags.filter(user=user)

    def get_title (self):
        """Returns the title of the site.

        The title is composed of the dedication, name and region.

        :rtype: `unicode`

        """
        region = sculpture.utils.get_first_name(self.get_region_traditional(),
                                                'region')
        dedication = sculpture.utils.get_first_name(self.get_dedication_now(),
                                                    'dedication')
        title = ', '.join([dedication, self.name, region])
        return title.strip(' ,')

    def _link_glossary (self):
        """Recreates links to the glossary within the rich text fields
        for this site.

        Changes the content of some fields on self, but does not save
        self.

        Changes, and saves, the Features of this site.

        """
        terms = GlossaryTerm.objects.get_regexps()
        all_used_terms = []
        for field in ('description', 'history', 'comments'):
            text, used_terms = sculpture.utils.add_glossary_terms(
                getattr(self, field), terms)
            setattr(self, field, text)
            all_used_terms.extend(used_terms)
        for feature in self.features.all():
            all_used_terms.extend(feature.link_glossary(terms))
            feature.save()
        return list(set(all_used_terms))

    def save (self, *args, **kwargs):
        # Relink glossary terms.
        glossary_set = False
        try:
            glossary_terms = self._link_glossary()
            glossary_set = True
        except:
            pass
        self._convert_refs()
        self._derive_gis_data()
        self.title = self.get_title()
        super(Site, self).save(*args, **kwargs)

        if glossary_set:
            # Set the glossary terms used in this site report.
            self.glossary_terms.clear()
            self.glossary_terms.add(*glossary_terms)

from haystack import indexes

import sculpture.constants
import sculpture.models


class BaseIndex (object):

    # Sadly fields cannot be specified on a parent class and be
    # inherited by its child classes.

    def prepare_dedications (self, site, period):
        data = []
        for site_dedication in site.sitededication_set.filter(
            period__name=period):
            data.append(site_dedication.dedication)
        return data

    def prepare_dioceses (self, site, period):
        data = []
        for site_diocese in site.sitediocese_set.filter(period__name=period):
            data.append(site_diocese.diocese)
        return data

    def prepare_dedications_medieval (self, site):
        return self.prepare_dedications(site, sculpture.constants.DATE_MEDIEVAL)

    def prepare_dedications_now (self, site):
        return self.prepare_dedications(site, sculpture.constants.DATE_NOW)

    def prepare_dioceses_medieval (self, site):
        return self.prepare_dioceses(site, sculpture.constants.DATE_MEDIEVAL)

    def prepare_dioceses_now (self, site):
        return self.prepare_dioceses(site, sculpture.constants.DATE_NOW)

    def prepare_regions (self, site, periods):
        data = []
        for site_region in site.siteregion_set.filter(period__name__in=periods):
            data.append(site_region.region.name)
        return data

    def prepare_regions_now (self, site):
        return self.prepare_regions(site, [sculpture.constants.DATE_NOW])

    def prepare_regions_traditional (self, site):
        return self.prepare_regions(site, [sculpture.constants.DATE_TRADITIONAL,
                                           sculpture.constants.DATE_TRADITIONAL_U,
                                           sculpture.constants.DATE_TRADITIONAL_I,
                                           sculpture.constants.DATE_TRADITIONAL_S,
                                           sculpture.constants.DATE_HISTORIC])


class FeatureImageIndex (BaseIndex, indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    country = indexes.CharField(faceted=True)
    dedications_medieval = indexes.MultiValueField(faceted=True)
    dedications_now = indexes.MultiValueField(faceted=True)
    dioceses_medieval = indexes.MultiValueField(faceted=True)
    dioceses_now = indexes.MultiValueField(faceted=True)
    feature_sets = indexes.MultiValueField(faceted=True)
    regions_now = indexes.MultiValueField(faceted=True)
    regions_traditional = indexes.MultiValueField(faceted=True)
    settlement = indexes.CharField(faceted=True, null=True)

    def get_model (self):
        return sculpture.models.FeatureImage

    def _get_site (self, feature_image):
        return feature_image.feature.site

    def index_queryset (self, using=None):
        published_statuses = [
            sculpture.constants.SITE_STATUS_PUBLISHED,
            sculpture.constants.SITE_STATUS_PUBLISHED_INCOMPLETE]
        return self.get_model().objects.filter(
            feature__site__status__name__in=published_statuses)

    def prepare_country (self, feature_image):
        site = self._get_site(feature_image)
        return str(site.country)

    def prepare_dedications_medieval (self, feature_image):
        site = self._get_site(feature_image)
        return super(FeatureImageIndex, self).prepare_dedications_medieval(site)

    def prepare_dedications_now (self, feature_image):
        site = self._get_site(feature_image)
        return super(FeatureImageIndex, self).prepare_dedications_now(site)

    def prepare_dioceses_medieval (self, feature_image):
        site = self._get_site(feature_image)
        return super(FeatureImageIndex, self).prepare_dioceses_medieval(site)

    def prepare_dioceses_now (self, feature_image):
        site = self._get_site(feature_image)
        return super(FeatureImageIndex, self).prepare_dioceses_now(site)

    def prepare_feature_sets (self, feature_image):
        return feature_image.feature.feature_set.get_title()

    def prepare_regions_now (self, feature_image):
        site = self._get_site(feature_image)
        return super(FeatureImageIndex, self).prepare_regions_now(site)

    def prepare_regions_traditional (self, feature_image):
        site = self._get_site(feature_image)
        return super(FeatureImageIndex, self).prepare_regions_traditional(site)

    def prepare_settlement (self, feature_image):
        site = self._get_site(feature_image)
        return str(site.settlement)


class SiteIndex (BaseIndex, indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    country = indexes.CharField(faceted=True, model_attr='country')
    dedications_medieval = indexes.MultiValueField(faceted=True)
    dedications_now = indexes.MultiValueField(faceted=True)
    dioceses_medieval = indexes.MultiValueField(faceted=True)
    dioceses_now = indexes.MultiValueField(faceted=True)
    feature_sets = indexes.MultiValueField(faceted=True)
    regions_now = indexes.MultiValueField(faceted=True)
    regions_traditional = indexes.MultiValueField(faceted=True)
    settlement = indexes.CharField(faceted=True, model_attr='settlement',
                                   null=True)
    glossary_terms = indexes.MultiValueField(faceted=True)
    location = indexes.LocationField(model_attr='location', null=True)
    latitude = indexes.FloatField(model_attr='latitude', null=True)
    longitude = indexes.FloatField(model_attr='longitude', null=True)

    def get_model (self):
        return sculpture.models.Site

    def index_queryset (self, using=None):
        published_statuses = [
            sculpture.constants.SITE_STATUS_PUBLISHED,
            sculpture.constants.SITE_STATUS_PUBLISHED_INCOMPLETE]

        return self.get_model().objects.filter(
            status__name__in=published_statuses)

    def prepare_feature_sets (self, site):
        data = []
        for feature_set in site.feature_sets():
            data.append(feature_set.get_title())
        return data

    def prepare_glossary_terms (self, site):
        return site.glossary_terms.all()

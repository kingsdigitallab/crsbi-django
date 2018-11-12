from django.db import models

from .base_model import BaseModel


class FeatureSetManager (models.Manager):

    def filter_by_site (self, site_id):
        """Returns a QuerySet of FeatureSets that are directly
        associated with Features associated with the Site having id
        `site_id`."""
        return self.filter(features__site=site_id).distinct()


class FeatureSet (BaseModel):

    order = models.IntegerField()
    name = models.CharField(max_length=64)
    feature_set = models.ForeignKey('self', blank=True, null=True,
                                    related_name='children')
    n = models.CharField(max_length=5, verbose_name='label')

    objects = FeatureSetManager()

    class Meta:
        app_label = 'sculpture'
        ordering = ['feature_set__name', 'order']
        unique_together = ('order', 'feature_set')

    def __str__ (self):
        hierarchy_name = ''
        feature_set = self.feature_set
        if feature_set:
            hierarchy_name = '%s: ' % str(feature_set)
        return '%s%s. %s' % (hierarchy_name, self.n, self.name)

    @models.permalink
    def get_absolute_url (self):
        return ('feature_set_display', [str(self.id)])

    def get_title (self):
        hierarchy_name = ''
        feature_set = self.feature_set
        if feature_set:
            hierarchy_name = '%s: ' % feature_set.get_title()
        return '%s%s' % (hierarchy_name, self.name)

    def sites (self):
        """Returns a QuerySet of published Sites that have Features
        directly associated with this FeatureSet."""
        from .site import Site
        return Site.published.filter_by_feature_set(self.id)

from django.core import urlresolvers
from django.db import models

import mezzanine.core.fields

import sculpture.utils
from .base_model import BaseModel
from .glossary_term import GlossaryTerm


class Feature (BaseModel):

    # QAZ: Old CRSBI allows for site to be empty. Why? How can that be
    # good?
    site = models.ForeignKey('Site', related_name='features')
    feature_set = models.ForeignKey('FeatureSet', related_name='features')
    name = models.CharField(max_length=100)
    description = mezzanine.core.fields.RichTextField(blank=True)
    order = models.IntegerField(editable=False)

    class Meta:
        app_label = 'sculpture'
        ordering = ['order', 'name']

    def __str__ (self):
        return '%s: %s' % (self.feature_set, self.name)

    def _calculate_order (self):
        """Returns the order order of this feature.

        :rtype: `int`

        """
        # Assumes that all FeatureSet order values are less than
        # 10. This could be enforced through model validation, but
        # that is likely overkill, since the legacy data has no values
        # higher than 5, and there is unlikely to be lots of new
        # FeatureSets.
        order = 0
        feature_set = self.feature_set
        multiplier = 1
        while feature_set is not None:
            order += feature_set.order * multiplier
            feature_set = feature_set.feature_set
            multiplier *= 10
        # Take into account the possibility that a feature is only one
        # or two deep in the feature set hierarchy, rather than three
        # levels deep.
        if order < 10:
            order *= 100
        elif order < 100:
            order *= 10
        return order

    # Edit link for use in the admin when a feature is edited inline.
    def edit_link (self):
        link = ''
        if self.id:
            url = urlresolvers.reverse('admin:sculpture_feature_change',
                                       args=(self.id,))
            link = '<a href="%s">change feature: images and description</a>' % url
        return link
    edit_link.allow_tags = True

    def get_feature_set_hierarchy (self):
        """Returns a list of the FeatureSets that make up the
        hierarchy for this feature.

        The list is ordered from top to bottom (ie, the first element
        is a FeatureSet that has no feature_set).

        """
        hierarchy = []
        feature_set = self.feature_set
        while feature_set is not None:
            hierarchy.append(feature_set)
            feature_set = feature_set.feature_set
        hierarchy.reverse()
        return hierarchy

    def link_glossary (self, terms):
        """Recreates links to the glossary within the rich text fields
        for this feature.

        This method does not save the change.

        :param terms: glossary terms
        :type terms: `dict`
        :rtype: `list`

        """
        self.description, used_terms = sculpture.utils.add_glossary_terms(
            self.description, terms)
        for detail in self.details.all():
            used_terms.extend(detail.link_glossary(terms))
        return used_terms

    def save (self, *args, **kwargs):
        # Recalculate the order of this feature.
        self.order = self._calculate_order()
        self.description = sculpture.utils.convert_refs_to_links(
            self.description)
        # This is inefficient, since the linking on Feature and Site
        # save. When edited through the admin, with inlines, this
        # leads to multiple saves. However, it does at least ensure
        # proper behaviour, which having only one or other
        # link-on-save does not.
        self.link_glossary(GlossaryTerm.objects.get_regexps())
        super(Feature, self).save(*args, **kwargs)

    def structured_dimensions (self):
        """Returns the dimensions associated with this feature
        structured into groups by section title."""
        data = {}
        for dimension in self.dimensions.all():
            section_data = data.setdefault(dimension.section, [])
            section_data.append(dimension)
        return data

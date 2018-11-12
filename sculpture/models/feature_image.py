from django.core import urlresolvers
from django.db import models

from .base_image import BaseImage
from .feature import Feature


class FeatureImage (BaseImage):

    feature = models.ForeignKey(Feature, related_name='images')

    class Meta (BaseImage.Meta):
        ordering = ['feature__site', 'feature', 'order']

    def __str__ (self):
        return self.caption or '[no caption]'

    # Edit link for use in the admin when a FeatureImage is edited inline.
    def edit_link (self):
        link = ''
        if self.id:
            url = urlresolvers.reverse('admin:sculpture_featureimage_change',
                                       args=(self.id,))
            link = '<a href="%s">Edit images and details</a>' % url
        return link
    edit_link.allow_tags = True
    edit_link.short_description = 'Edit details of image'

    def get_metadata (self):
        return super(FeatureImage, self).get_metadata(self.site())

    def site (self):
        """Returns the Site that this image ultimately belongs to."""
        return self.feature.site

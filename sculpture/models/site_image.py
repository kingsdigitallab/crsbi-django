from django.core import urlresolvers
from django.db import models

from .base_image import BaseImage
from .site import Site


class SiteImage (BaseImage):

    # Formerly the SculptureSiteImage model.

    site = models.ForeignKey(Site, related_name='images')

    class Meta (BaseImage.Meta):
        ordering = ['site', 'order']

    def __str__ (self):
        return self.caption or '[no caption]'

    # Edit link for use in the admin when a SiteImage is edited inline.
    def edit_link (self):
        link = ''
        if self.id:
            url = urlresolvers.reverse('admin:sculpture_siteimage_change',
                                       args=(self.id,))
            link = '<a href="%s">Edit images and details</a>' % url
        return link
    edit_link.allow_tags = True
    edit_link.short_description = 'Edit details of image'

    def get_metadata (self):
        return super(SiteImage, self).get_metadata(self.site)

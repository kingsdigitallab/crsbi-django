from django.db import models

import sculpture.constants
from .base_model import BaseModel
from .period import Period
from .region_type import RegionType


class Region (BaseModel):

    name = models.CharField(max_length=200)
    region_type = models.ForeignKey(RegionType, related_name='regions')

    class Meta:
        app_label = 'sculpture'
        ordering = ['name']
        unique_together = ('name', 'region_type')

    def __str__ (self):
        return '%s, %s' % (self.name, self.region_type.name)
        

    @models.permalink
    def get_absolute_url (self):
        return ('region_display', [str(self.id)])

    def get_sites_by_period (self, period_name):
        """Returns this diocese's Sites for the period `period_name`.

        :rtype: `QuerySet`

        """
        from .site import Site
        try:
            period = Period.objects.get(name=period_name)
        except Period.DoesNotExist:
            return Site.objects.none()
        return Site.objects.filter(regions=self,
                                   siteregion__period=period)

	
    def get_sites_traditional (self):
        """Returns this diocese's SiteDedications associated with the
        period "traditional".

        :rtype: `QuerySet`

        """
        return self.get_sites_by_period(sculpture.constants.DATE_TRADITIONAL)

    def get_sites_now (self):
        """Returns this diocese's SiteDedications associated with the
        period "now".

        :rtype: `QuerySet`

        """
        return self.get_sites_by_period(sculpture.constants.DATE_NOW)

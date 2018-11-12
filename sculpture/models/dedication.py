from django.db import models

import sculpture.constants
from .base_model import BaseModel
from .period import Period


class Dedication (BaseModel):

    name = models.CharField(max_length=200, unique=True)

    class Meta:
        app_label = 'sculpture'
        ordering = ['name']

    def __str__ (self):
        return self.name

    @models.permalink
    def get_absolute_url (self):
        return ('dedication_display', [str(self.id)])

    def get_sites_by_period (self, period_name):
        """Returns this diocese's Sites for the period `period_name`.

        :rtype: `QuerySet`

        """
        from .site import Site
        try:
            period = Period.objects.get(name=period_name)
        except Period.DoesNotExist:
            return Site.objects.none()
        return Site.objects.filter(dedications=self,
                                   sitededication__period=period)

    def get_sites_medieval (self):
        """Returns this diocese's SiteDedications associated with the
        period "medieval".

        :rtype: `QuerySet`

        """
        return self.get_sites_by_period(sculpture.constants.DATE_MEDIEVAL)

    def get_sites_now (self):
        """Returns this diocese's SiteDedications associated with the
        period "now".

        :rtype: `QuerySet`

        """
        return self.get_sites_by_period(sculpture.constants.DATE_NOW)

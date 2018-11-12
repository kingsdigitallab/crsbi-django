from django.db import models

from .base_model import BaseModel
from .period import Period
from .region import Region
from .site import Site


class SiteRegion (BaseModel):

    site = models.ForeignKey(Site)
    region = models.ForeignKey(Region)
    period = models.ForeignKey(Period)
    date = models.CharField(max_length=32, blank=True)

    class Meta:
        app_label = 'sculpture'

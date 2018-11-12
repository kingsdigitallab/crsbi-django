from django.db import models

from .base_model import BaseModel
from .site import Site


class ExternalSite (BaseModel):

    site = models.ForeignKey(Site)
    url = models.URLField('URL')
    title = models.CharField(max_length=128)

    class Meta:
        app_label = 'sculpture'

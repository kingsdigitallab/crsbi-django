from django.db import models

from .base_model import BaseModel
from .diocese import Diocese
from .period import Period
from .site import Site


class SiteDiocese (BaseModel):

    site = models.ForeignKey(Site)
    diocese = models.ForeignKey(Diocese)
    period = models.ForeignKey(Period)

    class Meta:
        app_label = 'sculpture'

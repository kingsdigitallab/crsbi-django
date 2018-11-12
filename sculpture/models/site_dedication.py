from django.db import models

from .base_model import BaseModel
from .dedication import Dedication
from .period import Period
from .site import Site


class SiteDedication (BaseModel):

    site = models.ForeignKey(Site)
    dedication = models.ForeignKey(Dedication)
    period = models.ForeignKey(Period)
    date = models.CharField(blank=True, max_length=32)
    certain = models.BooleanField(default=True)

    class Meta:
        app_label = 'sculpture'

    def __str__ (self):
        date = ''
        if self.date:
            date = ' (%s)' % self.date
        return ('%s%s' % (self.dedication, date))

from django.db import models

from .base_model import BaseModel
from .feature import Feature


class Dimension (BaseModel):

    feature = models.ForeignKey(Feature, related_name='dimensions')
    dimension_type = models.CharField(max_length=150)
    value = models.CharField(max_length=150)
    section = models.CharField(blank=True, max_length=150)
    order = models.IntegerField(default=2)

    class Meta:
        app_label = 'sculpture'
        ordering = ['dimension_type', 'feature', 'section', 'order']

    def __str__ (self):
        return '%s %s' % (self.dimension_type, self.value)

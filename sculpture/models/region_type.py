from django.db import models

from .base_model import BaseModel


class RegionType (BaseModel):

    # The name values specified in this table are also used in
    # sculpture.constants, and therefore need to be changed in both
    # places or neither.

    name = models.CharField(max_length=32, unique=True,
                            help_text='Changes to this value may require code changes also.')

    class Meta:
        app_label = 'sculpture'
        ordering = ['name']

    def __str__ (self):
        return self.name

from django.db import models

from .base_model import BaseModel


class Period (BaseModel):

    # Formerly the DateType model.

    # The name values specified in this table are also used in
    # sculpture.constants, and therefore need to be changed in both
    # places or neither.

    name = models.CharField(max_length=64, unique=True,
                            help_text='Changes to this value will require code changes also.')

    class Meta:
        app_label = 'sculpture'
        ordering = ['name']

    def __str__ (self):
        return self.name

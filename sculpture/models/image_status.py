from django.db import models

from .base_model import BaseModel


class ImageStatus (BaseModel):

    name = models.CharField(max_length=32, unique=True,
                            help_text='Changes to this value will require code changes also.')

    class Meta:
        app_label = 'sculpture'
        ordering = ['name']
        verbose_name_plural = 'image statuses'

    def __str__ (self):
        return self.name

from django.db import models

from .base_model import BaseModel


class Country (BaseModel):

    name = models.CharField(max_length=32, unique=True)

    class Meta:
        app_label = 'sculpture'
        ordering = ['name']
        verbose_name_plural = 'countries'

    def __str__ (self):
        return self.name

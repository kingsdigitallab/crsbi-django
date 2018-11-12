from django.db import models

from .base_model import BaseModel


class Settlement (BaseModel):

    name = models.CharField(max_length=200, unique=True)

    class Meta:
        app_label = 'sculpture'
        ordering = ['name']
        verbose_name = 'type of building / monument'
        verbose_name_plural = 'types of building / monument'

    def __str__ (self):
        return self.name

    @models.permalink
    def get_absolute_url (self):
        return ('settlement_display', [str(self.id)])

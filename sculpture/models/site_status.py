from django.db import models

import sculpture.constants
from .base_model import BaseModel
import sculpture.utils
import sculpture.models

class SiteManager (models.Manager):

    def filter_by_user (self, user):
        if not (user.is_superuser or sculpture.utils.get_profile(user).is_editor):
            objects = self.all().filter(name__in=sculpture.constants.FIELDWORKER_STATUSES_VISIBLE)
        else:
            objects = self.all()
        return objects


class SiteStatus (BaseModel):

    name = models.CharField(max_length=32, unique=True,
                            help_text='Changes to this value will require code changes also.')

    objects = SiteManager()

    class Meta:
        app_label = 'sculpture'
        ordering = ['name']
        verbose_name_plural = 'site statuses'

    def __str__ (self):
        return self.name

from django.db import models

from .base_model import BaseModel
from .user_profile import UserProfile


class Contributor (BaseModel):

    user_profile = models.OneToOneField(UserProfile, blank=True, null=True,
                                        related_name='contributor')
    name = models.CharField(max_length=128)

    class Meta:
        app_label = 'sculpture'
        ordering = ['name']

    def __str__ (self):
        return self.name

from django.db import models

from .base_model import BaseModel
from .site import Site
from .user_profile import UserProfile


class SiteTagManager (models.Manager):

    def filter_for_user (self, user):
        """Returns SiteTags associated with `user`.

        :param user: user profile
        :type user: `UserProfile`
        :rtype: `QuerySet`

        """
        return self.get_queryset().filter(user=user)


class SiteTag (BaseModel):

    user = models.ForeignKey(UserProfile, editable=False)
    tag = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    sites = models.ManyToManyField(Site, editable=False, related_name='tags')

    objects = SiteTagManager()

    class Meta:
        app_label = 'sculpture'
        ordering = ['tag']
        unique_together = ('user', 'tag')

    def __str__ (self):
        return self.tag

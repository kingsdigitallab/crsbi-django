from django.db import models

from .base_model import BaseModel


class SiteCommentManager (models.Manager):

    def filter_for_user (self, user):
        """Returns SiteComments associated with `user`.

        :param user: user profile
        :type user: `UserProfile`
        :rtype: `QuerySet`

        """
        return self.get_queryset().filter(user=user)


class SiteComment (BaseModel):

    site = models.ForeignKey('Site', editable=False)
    user = models.ForeignKey('UserProfile', editable=False)
    comment = models.TextField()

    objects = SiteCommentManager()

    class Meta:
        app_label = 'sculpture'
        ordering = ['modified']
        unique_together = ('site', 'user')

    def __str__ (self):
        return self.comment

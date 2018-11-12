from django.db import models

from .base_model import BaseModel


class UserFeedback (BaseModel):

    # page stores a app-root relative URL of the page the comment was
    # submitted from.
    page = models.CharField(max_length=255)
    feedback = models.TextField()

    class Meta:
        app_label = 'sculpture'
        ordering = ['-created']
        verbose_name_plural = 'user feedback'

    def __str__ (self):
        return self.feedback

    def page_link (self):
        return '<a href="%s">%s</a>' % (self.page, self.page)
    page_link.allow_tags = True

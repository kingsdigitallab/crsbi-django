from django.db import models


class BaseModel (models.Model):

    """Abstract base model that provides common fields."""

    created = models.DateTimeField('date created', auto_now_add=True)
    modified = models.DateTimeField('date modified', auto_now=True)

    class Meta:
        abstract = True
        app_label = 'sculpture'

from django.db import models

import mezzanine.core.fields

import sculpture.utils
from .base_model import BaseModel
from .feature import Feature


class Detail (BaseModel):

    feature = models.ForeignKey(Feature, related_name='details')
    title = models.CharField(max_length=200)
    text = mezzanine.core.fields.RichTextField(blank=True)
    order = models.IntegerField(default=2)

    class Meta:
        app_label = 'sculpture'
        ordering = ['order', 'title']

    def __str__ (self):
        return self.title

    def link_glossary (self, terms):
        """Recreates links to the glossary within the rich text fields
        for this detail.

        This method saves the change.

        :param terms: glossary terms
        :type terms: `dict`
        :rtype: `list`

        """
        self.text, used_terms = sculpture.utils.add_glossary_terms(
            self.text, terms)
        self.save()
        return used_terms

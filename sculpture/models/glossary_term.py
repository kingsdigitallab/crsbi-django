import re

from django.db import models

import mezzanine.core.fields

import iipimage.fields
import iipimage.storage

from .base_model import BaseModel


class GlossaryTermManager (models.Manager):

    def get_regexps (self):
        """Returns a dictionary of regular expressions keyed to
        GlossaryTerm ids.

        The regular expressions are matches for the names of each
        GlossaryTerm.

        :rtype: `dict`

        """
        terms = {}
        for term in self.all().prefetch_related('synonyms'):
            synonyms = list(term.synonyms.values_list('name', flat=True)) \
                + [term.name]
            # There should always be surrounding HTML markup in the
            # text this pattern applies to, so there is no need to
            # worry about the pattern not matching the start of a
            # string.
            for synonym in synonyms:
                pattern = r'''(?<=\W)(%s)(?=[ ,:;.?!'"])''' % re.escape(synonym)
                terms[re.compile(pattern, re.IGNORECASE)] = term.id
        return terms


class GlossaryTerm (BaseModel):

    name = models.CharField(max_length=64, unique=True)
    broader_term = models.ForeignKey('GlossaryTerm', blank=True, null=True,
                                     related_name='narrower_terms')
    description = mezzanine.core.fields.RichTextField()
    image = iipimage.fields.ImageField(
        null=True, blank=True, storage=iipimage.storage.image_storage,
        upload_to=iipimage.storage.get_image_path)

    objects = GlossaryTermManager()

    class Meta:
        app_label = 'sculpture'
        ordering = ['name']

    def __str__ (self):
        return self.name

    @models.permalink
    def get_absolute_url (self):
        return ('glossary_term_display', [str(self.id)])

    def display_synonyms (self):
        return self.synonyms.filter(display=True)

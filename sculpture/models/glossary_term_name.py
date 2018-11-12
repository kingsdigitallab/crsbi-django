from django.db import models

from .base_model import BaseModel
from .glossary_term import GlossaryTerm


class GlossaryTermName (BaseModel):

    glossary_term = models.ForeignKey(GlossaryTerm, related_name='synonyms')
    name = models.CharField(max_length=64, unique=True)
    display = models.BooleanField(
        default=True, help_text='Whether to list this name as a synonym')

    class Meta:
        app_label = 'sculpture'
        ordering = ['name']
        verbose_name = 'glossary term synonym'

    def __str__ (self):
        return self.name

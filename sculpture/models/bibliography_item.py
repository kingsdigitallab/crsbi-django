from django.db import models

import mezzanine.core.fields

from .base_model import BaseModel
from .site import Site


class BibliographyItem (BaseModel):

    """Model representing an item or entry in a bibliography."""

    site = models.ForeignKey(Site, related_name='bibliography_items')
    name = mezzanine.core.fields.RichTextField(help_text='Eg: N. Pevsner, The Buildings of England: Herefordshire, Harmondsworth, 1963, 78')
    sort_under = models.CharField(blank=True, max_length=32,
                                  help_text='Text used for sorting this entry; eg: Pevsner, N.')

    class Meta:
        app_label = 'sculpture'
        ordering = ['sort_under', 'name']

    def __str__ (self):
        return self.name

import re

from django.db import models

import requests


class ImageFieldFile (models.fields.files.ImageFieldFile):

    @property
    def full_base_url (self):
        return self.storage.full_base_url(self.name)

    def _get_image_dimensions (self):
        if not hasattr(self, '_dimensions_cache'):
            height = width = 0
            dimension_url = self.storage.full_base_url(self.name)
            r = requests.get(dimension_url)
            matches = re.match(r'^.*?Max-size:(\d+)\s+(\d+).*?$',
                               r.text.strip())
            if matches:
                width = int(matches.group(1))
                height = int(matches.group(2))
            self._dimensions_cache = width, height
        return self._dimensions_cache

    def thumbnail_url (self, height=None, width=None):
        try:
            height = str(int(height))
        except (TypeError, ValueError):
            height = ''
        try:
            width = str(int(width))
        except (TypeError, ValueError):
            width = ''
        return '%s/full/%s,%s/0/default.jpg' % (self.full_base_url, width, height)


class ImageField (models.ImageField):

    attr_class = ImageFieldFile




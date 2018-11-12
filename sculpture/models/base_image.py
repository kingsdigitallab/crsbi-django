from django.db import models

import iipimage.fields
import iipimage.storage

import sculpture.constants

from .base_model import BaseModel
from .contributor import Contributor
from .image_status import ImageStatus


class BaseImage (BaseModel):

    """Abstract model for all images."""

    SOURCE_FORMATS = (('analogue', 'Analogue'), ('digital', 'Digital'))

    image = iipimage.fields.ImageField(
        height_field='height', width_field='width',
        storage=iipimage.storage.image_storage,
        upload_to=iipimage.storage.get_image_path,
        help_text='Accepts RAW, TIFF and JPEG files',
        blank=True,
        null=True)
    status = models.ForeignKey(
        ImageStatus, related_name='%(app_label)s_%(class)s_images', blank=True)
    photographer = models.ForeignKey(
        Contributor, blank=True, null=True,
        related_name='%(app_label)s_%(class)s_images')
    caption = models.CharField(blank=True, max_length=256)
    description = models.TextField(blank=True)
    source_format = models.CharField(blank=True, choices=SOURCE_FORMATS,
                                     max_length=12)
    upload_file_format = models.CharField(blank=True, max_length=10)
    upload_filename = models.CharField(blank=True, max_length=128)
    resolution = models.IntegerField(blank=True, help_text='Pixels per inch.',
                                     null=True)
    # width and height are automatically set (via height_field and
    # width_field on self.image). The information may still be useful
    # to see, so do not set editable=False.
    width = models.IntegerField(help_text='Width in pixels.', blank=True)
    height = models.IntegerField(help_text='Height in pixels.', blank=True)
    bit_depth = models.CharField(blank=True, max_length=12)
    colour_mode = models.CharField(blank=True, max_length=12)
    camera_details = models.CharField(blank=True, max_length=256)
    photo_date = models.CharField(
        blank=True, help_text='Date the photo was taken (eg: 01 Jan 2013).',
        max_length=32)
    editing_software = models.CharField(blank=True, max_length=128)
    editing_notes = models.TextField(blank=True)
    order = models.IntegerField(default=2)
    copyright = models.TextField(blank=True, verbose_name="Copyright Information")

    class Meta:
        abstract = True
        app_label = 'sculpture'
        ordering = ['order']

    def __str__ (self):
        return self.caption

    def save (self, *args, **kwargs):
        # Automatically populate various metadata fields based on the
        # image file.
        if not self.id:
            # Set a status for the image.
            self.status = ImageStatus.objects.get(
                name=sculpture.constants.IMAGE_STATUS_GOOD)
        super(BaseImage, self).save(*args, **kwargs)

    def get_metadata (self, site):
        """Returns a dictionary of metadata for this image."""
        metadata = {'filename': self.image.name, 'caption': self.caption,
                    'date': self.photo_date, 'visit date': site.visit_date}
        contributors = '; '.join([author.name for author in site.authors.all()])
        metadata['fieldworkers'] = contributors
        if self.photographer:
            metadata['photographer'] = self.photographer.name
        for field, value in metadata.items():
            if value is not None:
                metadata[field] = value.encode('utf-8')
        return metadata

    # Linked thumbnail for use in the admin.
    # Adapted from http://djangosnippets.org/snippets/162/
    def linked_thumbnail (self):
        """Displays thumbnail-size image linked to the full image."""
        html = ''
        if self.id:
            html = '<a href="%s">%s</a>' % (self.image.url, self.thumbnail(70))
        return html
    linked_thumbnail.allow_tags = True

    def thumbnail (self, height=500):
        """Displays thumbnail-size image."""
        html = ''
        if self.id:
            image = self.image
            thumbnail_url = image.thumbnail_url(height=height)
            html = '<div  overflow: hidden;"><img height="%d"  src="%s"></div>' % (height, thumbnail_url)
        return html
    thumbnail.allow_tags = True

    # Linked thumbnail for use in the admin.
    # Adapted from http://djangosnippets.org/snippets/162/
    def thumbnail_site (self):
        """Displays thumbnail-size image linked to the full image."""
        html = ''
        if self.id:
            html = '<a href="%s" title="Photograph by: %s">%s</a>' % (self.image.url, self.photographer, self.thumbnail(640))
        return html
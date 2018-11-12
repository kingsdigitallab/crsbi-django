# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-01-16 13:33
from __future__ import unicode_literals

from django.db import migrations
import iipimage.fields
import iipimage.storage


class Migration(migrations.Migration):

    dependencies = [
        ('sculpture', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='featureimage',
            name='image',
            field=iipimage.fields.ImageField(height_field='height', help_text='Accepts RAW, TIFF and JPEG files', storage=iipimage.storage.ImageStorage(base_url='http://loris.kdl.kcl.ac.uk/crsbi/images', location='/vol/crsbi/images/'), upload_to=iipimage.storage.get_image_path, width_field='width'),
        ),
        migrations.AlterField(
            model_name='glossaryterm',
            name='image',
            field=iipimage.fields.ImageField(blank=True, null=True, storage=iipimage.storage.ImageStorage(base_url='http://loris.kdl.kcl.ac.uk/crsbi/images', location='/vol/crsbi/images/'), upload_to=iipimage.storage.get_image_path),
        ),
        migrations.AlterField(
            model_name='siteimage',
            name='image',
            field=iipimage.fields.ImageField(height_field='height', help_text='Accepts RAW, TIFF and JPEG files', storage=iipimage.storage.ImageStorage(base_url='http://loris.kdl.kcl.ac.uk/crsbi/images', location='/vol/crsbi/images/'), upload_to=iipimage.storage.get_image_path, width_field='width'),
        ),
    ]
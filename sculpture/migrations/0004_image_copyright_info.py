# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-04-06 10:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sculpture', '0003_site_fieldworker_may_2017'),
    ]

    operations = [
        migrations.AddField(
            model_name='featureimage',
            name='copyright',
            field=models.TextField(blank=True, verbose_name='Copyright Information'),
        ),
        migrations.AddField(
            model_name='siteimage',
            name='copyright',
            field=models.TextField(blank=True, verbose_name='Copyright Information'),
        ),
    ]
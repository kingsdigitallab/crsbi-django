"""Command to delete unreferenced image files."""

import errno
import glob
import os

from django.conf import settings
from django.core.management.base import BaseCommand

import sculpture.models


class Command (BaseCommand):

    def handle (self, *args, **options):
        cwd = os.getcwd()
        os.chdir(settings.IMAGE_SERVER_ROOT)
        for name in glob.iglob('*/*.jp2'):
            if not self._is_referenced(name):
                try:
                    os.remove(name)
                except OSError, e:
                    if e.errno != errno.ENOENT:
                        raise
        os.chdir(cwd)

    def _is_referenced (self, name):
        if sculpture.models.SiteImage.objects.filter(image=name).count():
            return True
        if sculpture.models.FeatureImage.objects.filter(image=name).count():
            return True
        if sculpture.models.GlossaryTerm.objects.filter(image=name).count():
            return True
        return False

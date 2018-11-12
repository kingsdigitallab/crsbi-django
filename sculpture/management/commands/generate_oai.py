"""Generate OAI-PMH records suitable for use by CultureGrid and ArchSearch.

CultureGrid's requirements are specified at
http://www.ukoln.ac.uk/metadata/pns/pndsdcap/

"""

import glob
import os

from django.conf import settings
from django.core.management.base import BaseCommand

import sculpture.management.oai_pmh_site
import sculpture.models


class Command (BaseCommand):

    help = 'Generates and saves OAI-PMH records from the published Sites.'

    def handle (self, *args, **options):
        output_dir = settings.OAI_PMH_RECORD_DIR
        filenames = []
        for site in sculpture.models.Site.published.all():
            oai_pmh_record = sculpture.management.oai_pmh_site.OAIPMHSite(site)
            filename = oai_pmh_record.save(output_dir)
            filenames.append(filename)
        # Delete records that no longer correspond to a Site (eg,
        # records for now deleted Sites).
        for path in glob.glob(os.path.join(output_dir, '*.xml')):
            if path not in filenames:
                os.remove(path)

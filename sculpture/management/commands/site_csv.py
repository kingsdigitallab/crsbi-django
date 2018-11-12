"""Generate CSV version of database

"""

import glob
import os

from django.conf import settings
from django.core.management.base import BaseCommand

import sculpture.management.oai_pmh_site
import sculpture.models


class Command (BaseCommand):

    help = 'Generates CSV version of sites.'

    def handle (self, *args, **options):
        rows = []
        rows.append("ID,Site Name,Region,Country,Grid Reference,URL")
        for site in sculpture.models.Site.published.all():
        	rows.append(str(site.id) + "," + "\"" + site.name + "\",\"" + site.regions.all()[0].name + "\"," + site.country.name + "," + site.grid_reference + "," + "http://www.crsbi.ac.uk/site/" + str(site.id))
       
       	for row in rows:
        	print row

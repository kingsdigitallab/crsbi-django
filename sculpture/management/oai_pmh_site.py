"""Provides a class for generating PNDS_DC OAI-PMH records for Site
objects."""

import os.path

from lxml import etree

import django.contrib.sites.models
from django.db.models import Q
from django.utils.html import strip_tags

import sculpture.models
import sculpture.utils


# XML Namespaces.
DC_NAMESPACE = 'http://purl.org/dc/elements/1.1/'
DC = '{%s}' % DC_NAMESPACE
DC_TERMS_NAMESPACE = 'http://purl.org/dc/terms/'
DC_TERMS = '{%s}' % DC_TERMS_NAMESPACE
PNDS_DC_NAMESPACE = 'http://purl.org/mla/pnds/pndsdc/'
PNDS_DC = '{%s}' % PNDS_DC_NAMESPACE
XML_NAMESPACE = 'http://www.w3.org/XML/1998/namespace'
XML = '{%s}' % XML_NAMESPACE
XSI_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'
XSI = '{%s}' % XSI_NAMESPACE

NSMAP = {
    'dc': DC_NAMESPACE,
    'dcterms': DC_TERMS_NAMESPACE,
    'pndsdc': PNDS_DC_NAMESPACE,
    'xml': XML_NAMESPACE
    }

# Constant DC data.
LANGUAGE = 'en-GB'
LICENSE = 'http://creativecommons.org/licenses/by-nc-nd/2.0/uk/'
PUBLISHER = 'Corpus of Romanesque Sculpture in Britain and Ireland'
RIGHTS_HOLDER = 'Corpus of Romanesque Sculpture in Britain and Ireland'


class OAIPMHSite (object):

    def __init__ (self, site):
        self._site = site
        self._root = etree.Element(PNDS_DC + 'description', nsmap=NSMAP)
        self._root.set(XSI + 'schemaLocation', 'http://purl.org/mla/pnds/pndsdc/ http://www.ukoln.ac.uk/metadata/pns/pndsdcxml/2005-06-13/xmls/pndsdc.xsd')
        self._generate_record()

    def _create_contributors (self):
        site_query = Q(sculpture_siteimage_images__site=self._site)
        feature_query = Q(sculpture_featureimage_images__feature__site=self._site)
        photographers = sculpture.models.Contributor.objects.filter(
            site_query | feature_query).exclude(sites=self._site).distinct()
        for photographer in photographers:
            contributor = etree.SubElement(self._root, DC + 'contributor',
                                           nsmap=NSMAP)
            contributor.text = self._get_contributor_name(photographer)

    def _create_creators (self):
        for contributor in self._site.authors.all():
            name = self._get_contributor_name(contributor)
            creator = etree.SubElement(self._root, DC + 'creator', nsmap=NSMAP)
            creator.text = name

    def _create_description (self):
        description = etree.SubElement(self._root, DC + 'description',
                                       nsmap=NSMAP)
        description.set(XML + 'lang', 'en')
        name = self._site.name
        region = sculpture.utils.get_first_name(
            self._site.get_region_traditional(), 'region')
        country = str(self._site.country)
        if region:
            place = '%s, %s' % (region, country)
        else:
            place = country
        intro = 'Site record describing %s in %s.' % (name, place)
        intro += " The site's description is as follows. "
        text = strip_tags(self._site.description)
        description.text = intro + text

    def _create_format (self):
        format = etree.SubElement(self._root, DC + 'format', nsmap=NSMAP)
        format.set('encSchemeURI', 'http://purl.org/dc/terms/IMT')
        format.text = 'text/html'

    def _create_identifier (self):
        identifier = etree.SubElement(self._root, DC + 'identifier',
                                      nsmap=NSMAP)
        identifier.set('encSchemeURI', 'http://purl.org/dc/terms/URI')
        identifier.text = self._get_full_uri()

    def _create_language (self):
        language = etree.SubElement(self._root, DC + 'language', nsmap=NSMAP)
        language.set('encSchemeURI', 'http://purl.org/dc/terms/RFC4646')
        language.text = LANGUAGE

    def _create_license (self):
        license = etree.SubElement(self._root, DC_TERMS + 'license',
                                   nsmap=NSMAP)
        license.set('valueURI', LICENSE)

    def _create_publisher (self):
        publisher = etree.SubElement(self._root, DC + 'publisher', nsmap=NSMAP)
        publisher.text = PUBLISHER

    def _create_rights_holder (self):
        rights_holder = etree.SubElement(self._root, DC_TERMS + 'rightsHolder',
                                         nsmap=NSMAP)
        rights_holder.text = RIGHTS_HOLDER

    def _create_spatial_coverage (self):
        grid_reference = self._site.grid_reference
        if grid_reference:
            spatial = etree.SubElement(self._root, DC_TERMS + 'spatial',
                                       nsmap=NSMAP)
            spatial.set('encSchemeURI',
                        'http://purl.org/mla/pnds/terms/OSGridRef')
            spatial.text = grid_reference

    def _create_subjects (self):
        terms = ['Romanesque sculpture', self._site.name]
        for term in terms:
            subject = etree.SubElement(self._root, DC + 'subject', nsmap=NSMAP)
            subject.text = term

    def _create_temporal_coverage (self):
        pass

    def _create_title (self):
        title = etree.SubElement(self._root, DC + 'title', nsmap=NSMAP)
        title.set(XML + 'lang', 'en')
        title.text = 'Sculpture site record for %s' % self._site.name

    def _create_type (self):
        resource_type = etree.SubElement(self._root, DC + 'type', nsmap=NSMAP)
        resource_type.set('encSchemeURI', 'http://purl.org/dc/terms/DCMIType')
        resource_type.set('valueURI', 'http://purl.org/dc/dcmitype/Collection')
        resource_type.text = 'Collection'

    def _generate_record (self):
        self._create_identifier()
        self._create_title()
        self._create_description()
        self._create_subjects()
        self._create_type()
        self._create_license()
        self._create_rights_holder()
        self._create_creators()
        self._create_contributors()
        self._create_publisher()
        self._create_language()
        self._create_spatial_coverage()
        self._create_temporal_coverage()
        self._create_format()

    def _get_contributor_name (self, contributor):
        """Return the name of contributor, by preference in
        'last_name, first_name' format."""
        name = str(contributor)
        if contributor.user_profile:
            user = contributor.user_profile.user
            first_name = user.first_name
            last_name = user.last_name
            if last_name:
                name = last_name
                if first_name:
                    name = name + ', ' + first_name
        return name

    def _get_full_uri (self):
        domain = django.contrib.sites.models.Site.objects.get_current().domain
        return 'http://%s%s' % (domain, self._site.get_absolute_url())

    def _is_record_changed (self, path, record):
        """Returns True if `record` differs from the record at `path`."""
        if os.path.exists(path):
            fh = open(path, 'rU')
            old_record = fh.read()
            fh.close()
            return old_record != record
        return True

    def save (self, output_dir):
        """Serialises the record and saves it to `output_dir`."""
        record = etree.tostring(self._root, encoding='utf-8', pretty_print=True,
                                xml_declaration=True)
        path = os.path.join(output_dir, str(self._site.id) + '.xml')
        # Do not save a record that is the same as an existing record.
        if self._is_record_changed(path, record):
            fh = open(path, 'w')
            fh.write(record)
            fh.close()
        return path

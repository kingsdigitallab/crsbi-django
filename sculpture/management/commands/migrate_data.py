"""Command to migrate data from the old CRSBI model structure to the new.

The old models (with data) must exist in the project under the app
name "legacy". The legacy UserProfile model has a one-to-one
relationship with the User model, so that data must be present in the
"django.contrib.auth" app also.

legacy/models.py needs to be slightly modified from its form in the
old CRSBI repository. The UserProfile user field needs to have a
related_name specified ('legacy_user_profile' is a suitable value), or
else there will be a conflict with the sculpture app's UserProfile
reference to User.

This command also migrates glossary data from an XML file (expected to
be at legacy/glossary.xml) into the database. This file needs to be
modified from the original:

  * to ensure that every item to be migrated has an ID (the items for
    "arch", "capital" and "vault" do not).

  * to correct incorrect references ("screen" reference "parclose
    screen" with the wrong id)

This command also migrates site data from XML files (expected to be in
legacy/xml/) into the database.

When migrating images, information is checked from a mapping of legacy
filenames to new paths and metadata taken from the image metadata
database. The mapping is expected to be at legacy/archive_map.csv and
the database (a SQLite conversion of the original MS Access file) at
legacy/image-metadata.db.

This migration is designed to be run *once*, and with the expectation
that there is no meaningful data in the sculpture app - while the
migration is done in a transaction (for speed), if it fails part way
through, the proper course of action is to reset the sculpture app,
fix whatever problem caused the migration failure, and try again.

"""

import glob

from lxml import etree

from django.contrib.auth.models import User
from django.core import urlresolvers
from django.core.management.base import BaseCommand
from django.db import transaction
import django.db.models

import sculpture.constants
import sculpture.models
import sculpture.management.db_migrator
import sculpture.management.image_migrator
import sculpture.management.migration_utils as migration_utils
import sculpture.management.xml_migrator


class Command (BaseCommand):

    def __init__ (self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self._id_map = {}
        self._models = django.db.models.get_models(
            django.db.models.get_app('sculpture'))
        self._now = migration_utils.NOW

    def add_base_data (self):
        """Adds non-legacy data that is required for proper
        functioning of the site."""
        for status in (sculpture.constants.SITE_STATUS_PUBLISHED_INCOMPLETE,
                       sculpture.constants.SITE_STATUS_UNASSIGNED,
                       sculpture.constants.SITE_STATUS_UNREPORTED):
            site_status = sculpture.models.SiteStatus(name=status)
            site_status.save()
        for status in sculpture.constants.IMAGE_STATUSES:
            image_status = sculpture.models.ImageStatus(name=status)
            image_status.save()

    def add_constraints (self):
        for model in self._models:
            try:
                model._meta.get_field('created').auto_now_add = True
                model._meta.get_field('modified').auto_now = True
            except django.db.models.fields.FieldDoesNotExist:
                pass

    def create_user_profiles (self):
        """Creates UserProfile objects for each User."""
        for user in User.objects.all():
            try:
                sculpture.models.UserProfile.objects.get(user=user)
            except sculpture.models.UserProfile.DoesNotExist:
                sculpture.models.UserProfile.objects.create(user=user)

    def _get_object (self, model, model_name, legacy_id):
        object_id = self._id_map[model_name][legacy_id]
        return model.objects.get(id=object_id)

    @transaction.commit_on_success
    def handle (self, *args, **options):
        self.add_base_data()
        self.remove_constraints()
        self.create_user_profiles()
        # Migrate the glossary from an XML file. These are used when
        # saving Sites.
        self.migrate_glossary()
        self.migrate_database()
        self.add_constraints()
        # Migrate sites from XML files.
        self.migrate_xml_sites()
        # Generate new sites from image metadata.
        self.migrate_backlog_images()
        # Regenerate glossary links.
        self.link_glossary()

    def _is_glossary_simple_ref (self, item):
        """Returns True if `item` is described simply by reference to
        another term."""
        gloss = item.find('gloss')
        if gloss.text.lstrip() == 'See ' and len(gloss.xpath('ref')) == 1:
            return True
        return False

    def link_glossary (self):
        for site in sculpture.models.Site.objects.all():
            site.save()

    def migrate_backlog_images (self):
        """Creates new Sites (etc) from records in the image metadata
        database that refer to Sites that do not yet exist."""
        migrator = sculpture.management.image_migrator.ImageMigrator()
        migrator.migrate()

    def migrate_database (self):
        migrator = sculpture.management.db_migrator.DBMigrator(
            self._id_map, self._now)
        migrator.migrate()

    def migrate_glossary (self):
        self._id_map['glossary'] = {}
        tree = etree.parse('legacy/glossary.xml')
        # Because there are cross-references between glossary entries,
        # loop through them twice, adding the descriptions (where the
        # cross-references occur) on the second pass.
        for item in tree.xpath('//TEI.2/text/body/list/item[@id]'):
            # Some items are purely "see" references, and should
            # become alternate names of the referenced term rather
            # than terms themselves. Do not create a term here, and
            # add it to the referenced term's names in the next pass.
            if not self._is_glossary_simple_ref(item):
                term = self._migrate_glossary_term(item, None)
                # Loop through any sub-terms.
                for subitem in item.xpath('list/item[@id]'):
                    self._migrate_glossary_term(subitem, term)
        for item in tree.xpath('//TEI.2/text/body//item[@id]'):
            if self._is_glossary_simple_ref(item):
                term_id = item.find('gloss/ref').get('target')
                term = self._get_object(sculpture.models.GlossaryTerm,
                                        'glossary', term_id)
                synonym = sculpture.models.GlossaryTermName(
                    glossary_term=term, name=item.findtext('term').strip(),
                    created=self._now, modified=self._now)
                synonym.save()
            else:
                term = self._get_object(sculpture.models.GlossaryTerm,
                                        'glossary', item.get('id'))
                term.description = self._migrate_glossary_description(
                    item.find('gloss'))
                term.save()

    def _migrate_glossary_description (self, gloss):
        """Returns an HTML string of `gloss`.

        TEI ref elements are converted to HTML a elements, the
        surrounding gloss element is converted to a p, and extraneous
        whitespace is stripped.

        """
        # Many of the glosses start with a space, that should be removed.
        gloss.text = gloss.text.lstrip()
        # Change TEI ref elements to HTML links.
        ref = None
        for ref in gloss.iterfind('ref'):
            ref.tag = 'a'
            target_id = ref.get('target')
            target = self._get_object(sculpture.models.GlossaryTerm, 'glossary',
                                      target_id)
            target_url = urlresolvers.reverse('glossary_term_display',
                                              kwargs={'term_id': target.id})
            ref.set('href', target_url)
            del ref.attrib['target']
        # Remove trailing whitespace. Assumes that the only elements
        # in the gloss are refs.
        if ref is None:
            gloss.text = gloss.text.rstrip()
        else:
            ref.tail = ref.tail.rstrip()
        gloss.tag = 'p'
        gloss.tail = ''
        return etree.tostring(gloss, encoding='utf-8')

    def _migrate_glossary_term (self, item, parent):
        term = migration_utils.regularise_text(item.findtext('term'))
        # Setting the description here is necessary for validation,
        # but the text is overwritten later in the glossary migration
        # process.
        glossary_term = sculpture.models.GlossaryTerm(
            name=term, broader_term=parent, description='Lorem ipsum',
            created=self._now, modified=self._now)
        glossary_term.save()
        self._id_map['glossary'][item.get('id')] = glossary_term.id
        return glossary_term

    def migrate_xml_sites (self):
        xslt_tree = etree.parse('sculpture/management/preprocess_tei.xsl')
        transform = etree.XSLT(xslt_tree)
        for filename in glob.glob('legacy/xml/*.xml'):
            site = sculpture.management.xml_migrator.XMLMigrator(
                filename, transform)
            site.migrate()

    def remove_constraints (self):
        for model in self._models:
            try:
                model._meta.get_field('created').auto_now_add = False
                model._meta.get_field('modified').auto_now = False
            except django.db.models.fields.FieldDoesNotExist:
                pass

import re

from lxml import etree

from django.core import urlresolvers
from django.db.models import Q

import sculpture.constants
import sculpture.models


REMOVE_NESTED_LINKS = '''
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">
  <xsl:template match="a[ancestor::a]">
    <xsl:apply-templates />
  </xsl:template>
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" />
    </xsl:copy>
  </xsl:template>
</xsl:stylesheet>'''
TRANSFORM_REMOVE_NESTED_LINKS = etree.XSLT(etree.XML(REMOVE_NESTED_LINKS))

def get_profile(user):
    return sculpture.models.UserProfile.objects.get(user=user)

def add_glossary_terms (text, terms):
    """Finds and adds links to the glossary terms in `terms` within
    HTML `text`.

    `terms` is a dictionary of glossary term ids and regular
    expressions to match on.

    Returns the modified text and a list of glossary terms (ids)
    found.

    :param text: HTML text
    :type text: `unicode`
    :param terms: glossary terms
    :type terms: `dict`
    :rtype: `list`

    """
    used_terms = []
    # First all glossary links must be removed from the text.
    link_expression = re.compile(r'<a[^>]*class="glossary"[^>]*>([^<]*)</a>')
    text = link_expression.subn('\g<1>', text)[0]
    # Then add new links.
    expressions = list(terms.keys())
    expressions.sort(key=lambda s: len(s.pattern), reverse=True)
    for expression in expressions:
        term_id = terms[expression]
        url = urlresolvers.reverse('glossary_term_display',
                                   kwargs={'term_id': term_id})
        replacement = '<a class="glossary %s" href="%s">\g<1></a>' % \
            (term_id, url)
        text, count = expression.subn(replacement, text)
        if count:
            used_terms.append(term_id)
    # The TinyMCE widget does some automatic tidying that removes any
    # link containing other links, and in the process manages to
    # remove any non-link content of the surrounding link (such as a
    # space between two words that together form a term and are also
    # each terms). This is in all ways undesired behaviour, so fix it
    # here.
    #
    # The lxml HTML parser cannot be used here, since it will, on
    # parsing, automatically convert "<a><a>foo</a></a>" to
    # "<a></a><a>foo</a>". This means that any HTML-specific nonsense
    # (such as <br>) needs to be dealt with before parsing.
    # text = text.replace('<br>', '<br/>')
    # text = text.replace('&nbsp;', ' ')
    # html = etree.XML('<div>%s</div>' % text)
    # result_tree = TRANSFORM_REMOVE_NESTED_LINKS(html)
    # text = etree.tostring(result_tree, xml_declaration=False)[5:-6]
    return text, used_terms

def convert_ref_to_link (match):
    """Converts a reference to a model object to an HTML link.

    :param match: match on a reference
    :type match: `re.MatchObject`

    """
    model_name = match.group('model')
    obj_id = match.group('id')
    if model_name == 'site':
        try:
            site = sculpture.models.Site.objects.get(pk=obj_id)
            text = '<a href="%s">%s</a>' % (site.get_absolute_url(),
                                            site.name)
        except sculpture.models.Site.DoesNotExist:
            text = match.group()
    else:
        text = match.group()
    return text

def convert_refs_to_links (content):
    """Returns RTE `content` with references to model objects
    converted to HTML links."""
    return re.sub(sculpture.constants.MODEL_REFERENCE_PATTERN,
                  convert_ref_to_link, '{}'.format(content))

def get_first_name (queryset, attribute):
    """Returns the name value of the first object in `queryset`, or u''.

    :rtype: `unicode`

    """
    if queryset:
        name = getattr(queryset[0], attribute).name
    else:
        name = u''
    return name

def get_tag_display_base_url ():
    """Returns the base URL for tag display.

    The base URL is the URL for display of a specific tag, minus the
    part containing the tag's id.

    Note that if the URLconf for tag_display changes, this function
    will need to be adapted accordingly.

    """
    url = urlresolvers.reverse('tag_display', kwargs={'tag_id': 1})
    return url[:-2]

def get_user_feedback_form (request):
    """Returns a dictionary containing the UserFeedbackForm."""
    import sculpture.forms.display
    form = sculpture.forms.display.UserFeedbackForm(
        initial={'page': request.get_full_path()})
    return {'user_feedback_form': form}

def restrict_queryset_by_site_permissions (qs, request, query_prefix=''):
    current_user = request.user
    # A superuser can see everything.
    if not current_user.is_superuser:
        profile = get_profile(current_user)
        query = None
        try:
            contributor = profile.contributor
        except sculpture.models.Contributor.DoesNotExist:
            author_query = ''
        else:
            author_query_kwargs = {query_prefix + 'authors': contributor}
            author_query = Q(**author_query_kwargs)
        draft_status = sculpture.constants.SITE_STATUS_DRAFT
        visible_status = sculpture.constants.FIELDWORKER_STATUSES
        status_query_kwargs = {query_prefix + 'status__name__in': visible_status}
        if profile.is_editor:
            return qs.distinct()
        elif author_query:
            # Contributors can see only their own Sites (and related
            # objects) that are in Draft status.
            query = author_query & Q(**status_query_kwargs)
        # It is possible to have a staff user (can log into admin) who
        # is neither a superuser, editor, or contributor.
        if query:
            qs = qs.filter(query)
        else:
            qs = qs.none()
    return qs.distinct()

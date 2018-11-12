from django.conf.urls import  url
from django.views.generic import ListView
from django.views.generic import TemplateView

import haystack.forms
import haystack.query
import haystack.views

import sculpture.forms.search
import sculpture.models
import sculpture.views.search

import sculpture.views.display
import sculpture.views.mycrsbi



# General display URLs.
urlpatterns = [
    url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt')),
    # Add browse here
    url(r'^browse/$', sculpture.views.display.browse, name='browse'),
    url(r'^feedback/$', sculpture.views.display.user_feedback_submit, name='user_feedback_submit'),
    url(r'^dedication/(?P<dedication_id>\d+)/$', sculpture.views.display.dedication_display,
        name='dedication_display'),
    url(r'^diocese/(?P<diocese_id>\d+)/$', sculpture.views.display.diocese_display,
        name='diocese_display'),
    url(r'^feature_set/(?P<feature_set_id>\d+)/$', sculpture.views.display.feature_set_display,
        name='feature_set_display'),
    url(r'^glossary/$', ListView.as_view(
            model=sculpture.models.GlossaryTerm,
            template_name='sculpture/display/glossary.html'),
        name='glossary_display'),
    url(r'^glossary/js/$', sculpture.views.display.glossary_js, name='glossary_js'),
    url(r'^glossary/term/(?P<term_id>\d+)/$', sculpture.views.display.glossary_term_display,
        name='glossary_term_display'),
    url(r'^region/(?P<region_id>\d+)/$', sculpture.views.display.region_display,
        name='region_display'),
    url(r'^settlement/(?P<settlement_id>\d+)/$', sculpture.views.display.settlement_display,
        name='settlement_display'),
    url(r'^site/map/(?P<site_id>\d+)/$', sculpture.views.display.site_map_display, name='site_map_display'),
    url(r'^site/(?P<site_id>\d+)/$', sculpture.views.display.site_display, name='site_display'),
    url(r'^site/(?P<site_id>\d+)/comment/$', sculpture.views.display.site_comment,
        name='site_comment'),
    url(r'^site/(?P<site_id>\d+)/image/(?P<image_type>feature|site)/(?P<image_id>\d+)/$',
        sculpture.views.display.image_display, name='image_display'),
    url(r'^preview/site/(?P<site_id>\d+)/$', sculpture.views.display.site_display_preview,
        name='site_display_preview'),
]

# MyCRSBI URLs.
urlpatterns += [
    url(r'^mycrsbi/$', sculpture.views.mycrsbi.user_profile, name='user_profile'),
    url(r'^mycrsbi/addtag/(?P<site_id>\d+)/$', sculpture.views.mycrsbi.tag_add, name='tag_add'),
    url(r'^mycrsbi/removetag/(?P<site_id>\d+)/$', sculpture.views.mycrsbi.tag_remove,
        name='tag_remove'),
    # Be aware, if changing the pattern for tag_display, that it is
    # the subject of string manipulation in
    # sculpture.utils.get_tag_display_base_url.
    url(r'^mycrsbi/tag/(?P<tag_id>\d+)/$', sculpture.views.mycrsbi.tag_display, name='tag_display'),
    ]

# Search URLs.
base_sqs = haystack.query.SearchQuerySet().facet('country').facet('dedications_medieval').facet('dedications_now').facet('dioceses_medieval').facet('dioceses_now').facet('regions_now').facet('regions_traditional').facet('settlement').facet('feature_sets')
site_sqs = base_sqs.models(sculpture.models.Site).facet('glossary_terms')
image_sqs = base_sqs.models(sculpture.models.FeatureImage)

urlpatterns +=[
    url(r'^search/$', haystack.views.search_view_factory(
            view_class=sculpture.views.search.SiteFacetedSearchView,
            form_class=sculpture.forms.search.FacetedSearchForm,
            searchqueryset=site_sqs, template='search/search.html'),
        name='haystack_site_search'),
    url(r'^search/image/$', haystack.views.search_view_factory(
            view_class=sculpture.views.search.FacetedSearchView,
            form_class=sculpture.forms.search.FacetedSearchForm,
            searchqueryset=image_sqs, template='search/image_search.html'),
        name='haystack_image_search'),
]

"""Views for the public-facing parts of the sculpture app."""

from django.contrib.auth.decorators import login_required
from django.contrib.gis.measure import Distance
from django.core import urlresolvers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

import sculpture.forms.display
import sculpture.models
import sculpture.utils
import datetime

import string
from urllib.request import urlopen
from weasyprint import HTML, CSS
import sculpture.constants

def get_pdf(request):
    pdf_url = request.build_absolute_uri()
    pdf_url = pdf_url.replace('/pdf', '')

    html = urlopen(pdf_url).read()
    pdf = HTML(base_url=request.build_absolute_uri(), string=html).write_pdf(stylesheets=[CSS(string='* { float: none !important; } * { font-size:0.8rem;}  .restrictor-site img{width:10%;float:left;margin-right:1%;} img{width:50%;}')])

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;\
        filename="crsbi.pdf"'

    return response

def browse (request):
    per_page = 20

    try:
        region = request.GET['region']
    except:
        region = False

    try:
        page = int(request.GET['page'])
    except:
        page = 1

    published_statuses = [
        sculpture.constants.SITE_STATUS_PUBLISHED,
        sculpture.constants.SITE_STATUS_PUBLISHED_INCOMPLETE]

    sites = sculpture.models.Site.objects.filter(
            status__name__in=published_statuses).select_related('settlement')

    if region:
        sites = sites.filter(name__istartswith=region)

    count = sites.count()

    # page data
    num_pages = int(count / per_page) + 1

    # Make sure we're not OOB:
    if page < 1 or page > num_pages:
        page = 1

    if page > 1:
        page_prev = page - 1
    else:
        page_prev = False

    if page < num_pages:
        page_next = page + 1
    else:
        page_next = False

    # get them
    if count < ((page + 1) * per_page) - 1:
        to_fetch = count + ((page - 1) * per_page)
    else:
        to_fetch = per_page
    frm = (page-1)*per_page

    sites = sites[frm:frm+to_fetch]
    context = {"sites": sites, 'region': region,
               'page': page, 'num_pages': num_pages, 'page_next': page_next,
               'page_prev': page_prev, 'chars': string.ascii_uppercase,}
               
    #context.update(sculpture.utils.get_user_feedback_form(request))
    return render(request, 'sculpture/display/browse.html', context)


def dedication_display (request, dedication_id):
    dedication = get_object_or_404(sculpture.models.Dedication,
                                   pk=dedication_id)
    context = {'dedication': dedication,
               'medieval_sites': dedication.get_sites_medieval(),
               'now_sites': dedication.get_sites_now()}
    context.update(sculpture.utils.get_user_feedback_form(request))
    return render(request, 'sculpture/display/dedication.html', context)

def diocese_display (request, diocese_id):
    diocese = get_object_or_404(sculpture.models.Diocese, pk=diocese_id)
    context = {'diocese': diocese,
               'medieval_sites': diocese.get_sites_medieval(),
               'now_sites': diocese.get_sites_now()}
    context.update(sculpture.utils.get_user_feedback_form(request))
    return render(request, 'sculpture/display/diocese.html', context)

def feature_set_display (request, feature_set_id):
    feature_set = get_object_or_404(sculpture.models.FeatureSet,
                                    pk=feature_set_id)
    context = {'feature_set': feature_set}
    context.update(sculpture.utils.get_user_feedback_form(request))
    return render(request, 'sculpture/display/feature_set.html', context)

def glossary_js (request):
    """Returns an HTTP response containing JavaScript for displaying
    glossary tooltips."""
    glossary_terms = sculpture.models.GlossaryTerm.objects.all()
    context = {'terms': glossary_terms}
    return render(request, 'sculpture/display/glossary.js', context,
                  content_type='text/javascript')

def glossary_term_display (request, term_id):
    term = get_object_or_404(sculpture.models.GlossaryTerm, pk=term_id)
    context = {'term': term}
    context.update(sculpture.utils.get_user_feedback_form(request))
    return render(request, 'sculpture/display/glossary_term.html', context)

def image_display (request, site_id, image_type, image_id):
    site = get_object_or_404(sculpture.models.Site, pk=site_id)
    if image_type == 'feature':
        image = get_object_or_404(sculpture.models.FeatureImage,
                                  feature__site=site, pk=image_id)
        template = 'sculpture/display/feature_image.html'
    else:
        image = get_object_or_404(sculpture.models.SiteImage, pk=image_id,
                                  site=site)
        template = 'sculpture/display/site_image.html'
    context = {'image': image, 'site': site}
    return render(request, template, context)

def region_display (request, region_id):
    region = get_object_or_404(sculpture.models.Region, pk=region_id)
    context = {'region': region, 'now_sites': region.get_sites_now(),
               'traditional_sites': region.get_sites_traditional()}
    context.update(sculpture.utils.get_user_feedback_form(request))
    return render(request, 'sculpture/display/region.html', context)

def settlement_display (request, settlement_id):
    settlement = get_object_or_404(sculpture.models.Settlement,
                                   pk=settlement_id)
    context = {'settlement': settlement}
    context.update(sculpture.utils.get_user_feedback_form(request))
    return render(request, 'sculpture/display/settlement.html', context)

@login_required
@require_POST
def site_comment (request, site_id):
    site = get_object_or_404(sculpture.models.Site.published, pk=site_id)
    user = request.user.userprofile
    try:
        comment = sculpture.models.SiteComment.objects.get(site=site, user=user)
        is_saved = True
    except sculpture.models.SiteComment.DoesNotExist:
        comment = sculpture.models.SiteComment(site=site, user=user)
        is_saved = False
    form = sculpture.forms.display.SiteCommentForm(request.POST,
                                                   instance=comment)
    if form.is_valid():
        if request.POST.get('_save'):
            form.save()
        elif request.POST.get('_delete') and is_saved:
            comment.delete()
    return redirect(site)

# Full page map display
def site_map_display (request, site_id):
    site = get_object_or_404(sculpture.models.Site.published, pk=site_id)
    context = {'site': site}
    context['marker_data'] = []
    if site.location:
        context = add_marker_data(context,site)
    return render(request, 'sculpture/display/map.html', context)


# Add marker data to context
def add_marker_data(context,site):
    local_sites = sculpture.models.Site.objects.filter(
        location__distance_lte=(site.location, Distance(mi=15)))
    local_sites_data = []
    for local_site in local_sites:
        local_sites_data.append([
            [local_site.latitude, local_site.longitude],
            local_site.title, local_site.get_absolute_url()])
    context['marker_data'] = local_sites_data
    return context


def site_display (request, site_id):
    site = get_object_or_404(sculpture.models.Site.published, pk=site_id)
    user = request.user
    # Display search-related links.
    search_page = request.session.get('search_page')
    search_results = request.session.get('search_results')
    previous_site = None
    next_site = None
    try:
        index = search_results.index(int(site_id))
    except (AttributeError, ValueError):
        pass
    else:
        if index != 0:
            previous_site = urlresolvers.reverse(
                'site_display', kwargs={'site_id': search_results[index-1]})
        if index != len(search_results) - 1:
            next_site = urlresolvers.reverse(
                'site_display', kwargs={'site_id': search_results[index+1]})
    glossary_js_url = urlresolvers.reverse('glossary_js')
    context = {'next_site': next_site, 'previous_site': previous_site,
               'search_page': search_page, 'site': site,
               'glossary_js_url': glossary_js_url}
    # Get map data for local Sites.
    context['marker_data'] = []
    if site.location:
        context = add_marker_data(context,site)
    if user.is_authenticated():
        user_profile = user.userprofile
        # Tagging.
        # URLs for adding and removing tags.
        add_tag_url = urlresolvers.reverse('tag_add',
                                           kwargs={'site_id': site_id})
        remove_tag_url = urlresolvers.reverse('tag_remove',
                                              kwargs={'site_id': site_id})
        context['add_tag_url'] = add_tag_url
        context['all_tags'] = sculpture.models.SiteTag.objects.filter_for_user(
            user_profile)
        context['base_tag_url'] = sculpture.utils.get_tag_display_base_url()
        context['remove_tag_url'] = remove_tag_url
        context['tags'] = site.get_tags(user_profile)
        # Commenting.
        try:
            comment = sculpture.models.SiteComment.objects.get(
                site=site, user=user_profile)
        except sculpture.models.SiteComment.DoesNotExist:
            comment = None
        context['site_comment'] = comment
        context['site_comment_form'] = sculpture.forms.display.SiteCommentForm(
            instance=comment)
    context.update(sculpture.utils.get_user_feedback_form(request))
    return render(request, 'sculpture/display/site.html', context)

@login_required
def site_display_preview (request, site_id):
    qs = sculpture.models.Site.objects.all()
    qs = sculpture.utils.restrict_queryset_by_site_permissions(qs, request)
    site = get_object_or_404(qs, pk=site_id)
    context = {'site': site}
    return render(request, 'sculpture/display/site_preview.html', context)

@require_POST
def user_feedback_submit (request):
    form = sculpture.forms.display.UserFeedbackForm(request.POST)
    if form.is_valid():
        form.save()
        context = {'form': None, 'page': form.cleaned_data['page'],
                   'success': True}
    else:
        context = {'form': form, 'page': None, 'success': False}
    return render(request, 'sculpture/display/user_feedback_submit.html',
                  context)

"""Views for the MyCRSBI section of the site."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
import json as simplejson
from django.views.decorators.http import require_POST

import sculpture.constants
import sculpture.forms.mycrsbi
import sculpture.models


@login_required
@require_POST
def tag_add (request, site_id):
    """View to add a POSTed tag to a site.

    A string tag is POSTed.

    """
    site = get_object_or_404(sculpture.models.Site.published, pk=site_id)
    data = {}
    user = request.user.userprofile
    tag = request.POST.get('tag', '')
    if tag:
        try:
            site_tag = sculpture.models.SiteTag.objects.get(tag=tag, user=user)
        except sculpture.models.SiteTag.DoesNotExist:
            site_tag = sculpture.models.SiteTag(tag=tag, user=user)
            site_tag.save()
        site_tag.sites.add(site)
        data['id'] = site_tag.id
        data['tag'] = tag
    return HttpResponse(simplejson.dumps(data), mimetype='application/json')

@login_required
def tag_display (request, tag_id):
    user = request.user.userprofile
    user_tags = sculpture.models.SiteTag.objects.filter_for_user(user)
    site_tag = get_object_or_404(user_tags, id=tag_id)
    # Get a second copy of the SiteTag, and pass that to the
    # form. This avoids the problem whereby a failed save might still
    # show a changed tag/description on the page, because the instance
    # object is changed after the data is retrieved from the database
    # but before the template is rendered.
    site_tag_instance = get_object_or_404(user_tags, id=tag_id)
    context = {'site_tag': site_tag}
    if request.method == 'POST':
        form = sculpture.forms.mycrsbi.SiteTagForm(request.POST,
                                                   instance=site_tag_instance)
        if form.is_valid():
            form.save()
            return redirect('tag_display', tag_id=tag_id)
    else:
        form = sculpture.forms.mycrsbi.SiteTagForm(instance=site_tag)
    context['form'] = form
    return render(request, 'sculpture/mycrsbi/tag_display.html', context)

@login_required
@require_POST
def tag_remove (request, site_id):
    """View to remove a POSTed tag from a site.

    A SiteTag id is POSTED.

    """
    site = get_object_or_404(sculpture.models.Site.published, pk=site_id)
    data = {}
    user = request.user.userprofile
    tag_id = request.POST.get('tag_id', '')
    if tag_id:
        tag_id = int(tag_id)
        try:
            site_tag = sculpture.models.SiteTag(id=tag_id, user=user)
            site_tag.sites.remove(site)
            if not site_tag.sites.count():
                site_tag.delete()
        except sculpture.models.SiteTag.DoesNotExist:
            pass
        data['id'] = tag_id
    return HttpResponse(simplejson.dumps(data), mimetype='application/json')

@login_required
def user_profile (request):
    user_profile = request.user.userprofile
    contributor = None
    try:
        contributor = user_profile.contributor
    except:
        pass
    sites = []
    if contributor:
        authored_sites = sculpture.models.Site.objects.filter(
            authors=contributor)
        for site in authored_sites:
            # The URL depends on the status.
            sites.append({'name': site.get_title(),
                          'status': str(site.status),
                          'url': site.get_absolute_url()})
    context = {
        'site_comments': sculpture.models.SiteComment.objects.filter_for_user(
            user_profile),
        'profile': user_profile,
        'sites': sites,
        'tags': sculpture.models.SiteTag.objects.filter_for_user(user_profile)}
    return render(request, 'sculpture/mycrsbi/profile.html', context)

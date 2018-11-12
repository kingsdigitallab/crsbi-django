import csv
import os
import shlex
import shutil
import io
import subprocess
import tempfile
import zipfile
import datetime

from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from wsgiref.util import FileWrapper
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db import models

import sculpture.constants
import sculpture.forms.admin
import sculpture.models
import sculpture.signals
import sculpture.utils

from django.contrib.admin.filters import DateFieldListFilter

class CustomDateFieldListFilter(DateFieldListFilter):

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field_generic = '%s__' % field_path
        self.date_params = {k: v for k, v in params.items() if k.startswith(self.field_generic)}

        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        if isinstance(field, models.DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:       # field is a models.DateField
            today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        next_year = today.replace(year=today.year + 1, month=1, day=1)



        self.lookup_kwarg_since = '%s__gte' % field_path
        self.lookup_kwarg_until = '%s__lt' % field_path
        self.links = (
            (_('Any date'), {}),
            (_('Today'), {
                self.lookup_kwarg_since: str(today),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('Past 7 days'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=7)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('This month'), {
                self.lookup_kwarg_since: str(today.replace(day=1)),
                self.lookup_kwarg_until: str(next_month),
            }),
            (_('Past 3 Months'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=90)),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('This year'), {
                self.lookup_kwarg_since: str(today.replace(month=1, day=1)),
                self.lookup_kwarg_until: str(next_year),
            }),
        )
        if field.null:
            self.lookup_kwarg_isnull = '%s__isnull' % field_path
            self.links += (
                (_('No date'), {self.field_generic + 'isnull': 'True'}),
                (_('Has date'), {self.field_generic + 'isnull': 'False'}),
            )
        super(DateFieldListFilter, self).__init__(
            field, request, params, model, model_admin, field_path)

class HasDedicationListFilter (admin.SimpleListFilter):

    parameter_name = 'has_dedication'
    title = _('has dedication')

    def lookups (self, request, model_admin):
        return (('no', _('No')), ('yes', _('Yes')))

    def queryset (self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(dedications__isnull=False)
        if self.value() == 'no':
            return queryset.filter(dedications__isnull=True)


class HasDioceseListFilter (admin.SimpleListFilter):

    parameter_name = 'has_diocese'
    title = _('has diocese')

    def lookups (self, request, model_admin):
        return (('no', _('No')), ('yes', _('Yes')))

    def queryset (self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(dioceses__isnull=False)
        if self.value() == 'no':
            return queryset.filter(dioceses__isnull=True)


class HasFeatureImagesListFilter (admin.SimpleListFilter):

    parameter_name = 'has_feature_images'
    title = _('has feature images')

    def lookups (self, request, model_admin):
        return (('no', _('No')), ('yes', _('Yes')))

    def queryset (self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(features__images__isnull=False)
        if self.value() == 'no':
            return queryset.exclude(features__images__isnull=False)


class HasGridReferenceListFilter (admin.SimpleListFilter):

    parameter_name = 'has_grid_reference'
    title = _('has grid reference')

    def lookups (self, request, model_admin):
        return (('no', _('No')), ('yes', _('Yes')))

    def queryset (self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(grid_reference='')
        if self.value() == 'no':
            return queryset.filter(grid_reference='')


class HasSettlementListFilter (admin.SimpleListFilter):

    parameter_name = 'has_settlement'
    title = _('has settlement')

    def lookups (self, request, model_admin):
        return (('no', _('No')), ('yes', _('Yes')))

    def queryset (self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(settlement__isnull=False)
        if self.value() == 'no':
            return queryset.filter(settlement__isnull=True)


class HasSiteImagesListFilter (admin.SimpleListFilter):

    parameter_name = 'has_site_images'
    title = _('has site images')

    def lookups (self, request, model_admin):
        return (('no', _('No')), ('yes', _('Yes')))

    def queryset (self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(images__isnull=False)
        if self.value() == 'no':
            return queryset.exclude(images__isnull=False)


class HasTraditionalRegionListFilter (admin.SimpleListFilter):

    parameter_name = 'has_region'
    title = _('has traditional region')

    def lookups (self, request, model_admin):
        return (('no', _('No')), ('yes', _('Yes')))

    def queryset (self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(
                siteregion__period__name__icontains='traditional')
        if self.value() == 'no':
            return queryset.exclude(
                siteregion__period__name__icontains='traditional')


class IsPosssibleDuplicateListFilter (admin.SimpleListFilter):

    parameter_name = 'is_possible_duplicate'
    title = _('is possible duplicate')

    def lookups (self, requeset, model_admin):
        return (('yes', _('Yes')),)

    def queryset (self, request, queryset):
        if self.value() == 'yes':
            duplicate_ids = set()
            previous_data = (None, None, None)  # id, name, settlement
            for row in queryset.filter(settlement__isnull=False).order_by(
                    'name', 'settlement'):
                if (row.name, row.settlement) == previous_data[1:]:
                    duplicate_ids.add(previous_data[0])
                    duplicate_ids.add(row.id)
                previous_data = (row.id, row.name, row.settlement)
            return queryset.filter(id__in=list(duplicate_ids))


class MissingTextListFilter (admin.SimpleListFilter):

    parameter_name = 'missing_text'
    title = _('is missing text')

    def lookups (self, request, model_admin):
        return (('no', _('No')), ('yes', _('Yes')))

    def queryset (self, request, queryset):
        queries = Q(history='') | Q(description='')
        if self.value() == 'yes':
            return queryset.filter(queries)
        if self.value() == 'no':
            return queryset.exclude(queries)


class PeriodDedicationListFilter (admin.SimpleListFilter):

    def lookups (self, request, model_admin):
        dedications = sculpture.models.Dedication.objects.filter(sitededication__period=self._period).distinct()
        return [(dedication.id, dedication.name) for dedication in dedications]

    def queryset (self, request, queryset):
        if self.value():
            return queryset.filter(sitededication__dedication=self.value(),
                                   sitededication__period=self._period)


class NowDedicationListFilter (PeriodDedicationListFilter):

    title = _('dedication (now)')
    parameter_name = 'dedication_now'

    def __init__ (self, *args, **kwargs):
        self._period = sculpture.models.Period.objects.get(
            name=sculpture.constants.DATE_NOW)
        super(NowDedicationListFilter, self).__init__(*args, **kwargs)


class PeriodRegionListFilter (admin.SimpleListFilter):

    def lookups (self, request, model_admin):
        regions = sculpture.models.Region.objects.filter(siteregion__period=self._period).distinct()
        return [(region.id, region.name) for region in regions]

    def queryset (self, request, queryset):
        if self.value():
            return queryset.filter(siteregion__region=self.value(),
                                   siteregion__period=self._period)


class NowRegionListFilter (PeriodRegionListFilter):

    title = _('region (now)')
    parameter_name = 'region_now'

    def __init__ (self, *args, **kwargs):
        self._period = sculpture.models.Period.objects.get(name=sculpture.constants.DATE_NOW)
        super(NowRegionListFilter, self).__init__(*args, **kwargs)


class Pre1974RegionListFilter (PeriodRegionListFilter):

    title = _('region (pre-1974)')
    parameter_name = 'region_pre'

    def __init__ (self, *args, **kwargs):
        self._period = sculpture.models.Period.objects.get(name=sculpture.constants.DATE_TRADITIONAL)
        super(Pre1974RegionListFilter, self).__init__(*args, **kwargs)


class BibliographyItemInline (admin.StackedInline):

    model = sculpture.models.BibliographyItem
    extra = 4
    verbose_name = 'Bibliography Item'
    verbose_name_plural = 'Bibliography'


class DetailInline (admin.TabularInline):

    model = sculpture.models.Detail


class DimensionInline (admin.TabularInline):

    model = sculpture.models.Dimension


class ExternalSiteInline (admin.TabularInline):

    model = sculpture.models.ExternalSite


class FeatureImageInline (admin.StackedInline):
    # Removed order from fields temporarily .
    fields = ('feature', 'image', 'caption', 'linked_thumbnail', 'status',
              'photographer', 'photo_date', 'order', 'edit_link')
    readonly_fields = ['edit_link', 'linked_thumbnail', 'source_format',
                       'upload_file_format', 'upload_filename', 'width',
                       'height', 'bit_depth', 'colour_mode', 'status']
    model = sculpture.models.FeatureImage


class FeatureInline (admin.StackedInline):

    fields = ('site', 'feature_set', 'name', 'description', 'edit_link')
    readonly_fields = ['edit_link']
    model = sculpture.models.Feature


class GlossaryTermNameInline (admin.TabularInline):

    model = sculpture.models.GlossaryTermName


class SiteDedicationInline (admin.TabularInline):

    model = sculpture.models.SiteDedication
    extra = 2


class SiteDioceseInline (admin.TabularInline):

    model = sculpture.models.SiteDiocese
    extra = 2


class SiteImageInline (admin.StackedInline):
    # Removed order from fields temporarily .

    fields = ('site', 'image', 'caption', 'linked_thumbnail', 'status',
              'photographer', 'photo_date', 'order', 'edit_link')
    readonly_fields = ['edit_link', 'linked_thumbnail', 'source_format',
                       'upload_file_format', 'upload_filename', 'width',
                       'height', 'bit_depth', 'colour_mode', 'status']
    model = sculpture.models.SiteImage


class SiteRegionInline (admin.TabularInline):

    model = sculpture.models.SiteRegion
    extra = 2


class BaseImageAdmin (admin.ModelAdmin):

    def action_rotate_image (self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect('rotate_image/?ids=%s' % ','.join(selected))
    action_rotate_image.short_description = 'Rotate selected images 90 degrees'

    def _get_feature_choices (self, site):
        choices = []
        if site:
            choices = [(feature.id, str(feature)) for feature
                       in site.features.all()]
        return choices

    def _get_site_choices (self):
        return [(site.id, str(site)) for site in sculpture.models.Site.objects.all()]

    def get_readonly_fields (self, request, obj=None):
        fields = list(super(BaseImageAdmin, self).get_readonly_fields(
                request, obj))
        # If the user is a fieldworker, make the status field
        # read-only.
        user = request.user
        if not (user.is_superuser or sculpture.utils.get_profile(user).is_editor):
            fields.append('status')
        return fields

    def get_urls (self):
        urls = super(BaseImageAdmin, self).get_urls()
        extra_urls = [
            url(r'^rotate_image/$', self.admin_site.admin_view(
                self.rotate_image)),
        ]
        return extra_urls + urls

    def has_add_permission (self, request):
        return False

    def rotate_image (self, request):
        """View for rotating images."""
        image_ids = request.GET.get('ids', '')
        context = {}
        if request.POST:
            form = sculpture.forms.admin.RotateImageForm(request.POST)
            if form.is_valid():
                image_ids = form.cleaned_data['image_ids'].split(',')
                # Create the temporary directory within the images
                # directory to avoid problems with the system temp
                # directory not being on the same filesystem as the
                # images.
                temp_dir = tempfile.mkdtemp(dir=settings.IMAGE_SERVER_ROOT)
                for image_id in image_ids:
                    self._rotate_image(image_id, temp_dir)
                shutil.rmtree(temp_dir, ignore_errors=True)
                return redirect('admin:sculpture_%simage_changelist' %
                                self.image_type)
        else:
            data = {'image_ids': image_ids}
            form = sculpture.forms.admin.RotateImageForm(initial=data)
        context['form'] = form
        return render(request, 'sculpture/admin/rotate_image.html', context)

    def _rotate_image (self, image, temp_dir):
        filepath = os.path.join(settings.IMAGE_SERVER_ROOT, image.image.name)
        temp_path1 = os.path.join(temp_dir, 'rotated.tif')
        temp_path2 = os.path.join(temp_dir, 'rotated.jp2')
        rotate_command = sculpture.constants.ROTATE_JP2 % (
            filepath, temp_path1)
        convert_command = sculpture.constants.CONVERT_TO_JP2 % (
            temp_path1, temp_path2)
        try:
            subprocess.check_call(shlex.split(rotate_command))
        except subprocess.CalledProcessError:
            return
        try:
            subprocess.check_call(shlex.split(convert_command))
        except subprocess.CalledProcessError:
            return
        try:
            shutil.move(temp_path2, filepath)
        except OSError:
            return

class BibliographyItemAdmin (admin.ModelAdmin):

    actions = ['action_export_bibliography']

    def action_export_bibliography (self, request, queryset):
        temp = tempfile.TemporaryFile()
        seen = []
        for item in queryset:
            name = strip_tags(item.name.encode('utf-8'))
            if name not in seen:
                temp.write(name)
                temp.write('\n')
                seen.append(name)
        wrapper = FileWrapper(temp)
        response = HttpResponse(wrapper, content_type='text/plain')
        response['Content-Length'] = temp.tell()
        temp.seek(0)
        return response
    action_export_bibliography.short_description = \
        'Download plain text list of items'

    def get_queryset (self, request):
        """Returns a QuerySet of BibliographyItems viewable by the request
        user."""
        qs = super(BibliographyItemAdmin, self).get_queryset(request)
        current_user = request.user
        profile = sculpture.utils.get_profile(current_user)
        if not current_user.is_superuser and not profile.is_editor:
            try:
                contributor = profile.contributor
            except sculpture.models.Contributor.DoesNotExist:
                qs = qs.none()
            else:
                qs = qs.filter(site__authors=contributor)
        return qs.distinct()


class ContributorAdmin (admin.ModelAdmin):

    list_display = ('name', 'modified', 'created')


class CountryAdmin (admin.ModelAdmin):

    list_display = ('name', 'modified', 'created')


class DedicationAdmin (admin.ModelAdmin):

    list_display = ('name', 'modified', 'created')


class DimensionAdmin (admin.ModelAdmin):

    list_display = ('feature', 'dimension_type', 'value', 'section', 'modified',
                    'created')
    list_display_links = ('feature', 'dimension_type', 'value')
    readonly_fields = ['feature']


class DioceseAdmin (admin.ModelAdmin):

    list_display = ('name', 'modified', 'created')


class FeatureAdmin (admin.ModelAdmin):

    inlines = [FeatureImageInline, DetailInline, DimensionInline]
    list_display = ('name', 'feature_set', 'site', 'description', 'modified',
                    'created')
    list_display_links = ('name', 'feature_set')
    list_filter = ['feature_set']
    readonly_fields = ['site']
    search_fields = ['name', 'description', 'site__site_id', 'site__name']

    def bulk_image_upload (self, request, feature_id):
        # Custom view for performing a bulk upload of images to become
        # FeatureImages.
        feature = get_object_or_404(sculpture.models.Feature, pk=feature_id)
        if request.method == 'POST':
            form = sculpture.forms.admin.BulkFeatureImageUpload(
                request.POST, request.FILES)
            if form.is_valid():
                for image in request.FILES.getlist('image'):
                    form_data = form.cleaned_data
                    form_data.update({'feature': feature, 'image': image})
                    instance = sculpture.models.FeatureImage(**form_data)
                    instance.save()
                return redirect('admin:sculpture_feature_change', feature_id)
        else:
            form = sculpture.forms.admin.BulkFeatureImageUpload()
        context = {'form': form, 'add': True, 'title': 'Add FeatureImages'}
        return render(request, 'sculpture/admin/bulk_image_upload.html',
                      context)

    def get_urls (self):
        urls = super(FeatureAdmin, self).get_urls()
        extra_urls = [
            url(r'^(?P<feature_id>\d+)/bulk_image_upload/$',
                self.admin_site.admin_view(self.bulk_image_upload))
            ]
        return extra_urls + urls

    def has_add_permission (self, request):
        # Features must be added through the inline on the Site page.
        return False

    def get_queryset (self, request):
        """Returns a QuerySet of Features viewable by the request
        user."""
        qs = super(FeatureAdmin, self).get_queryset(request)
        return sculpture.utils.restrict_queryset_by_site_permissions(
            qs, request, 'site__')

    def response_change (self, request, obj):
        response = super(FeatureAdmin, self).response_change(request, obj)
        if '_save' in request.POST:
            response = redirect('admin:sculpture_site_change',
                                obj.site.id)
        return response


class FeatureImageAdmin (BaseImageAdmin):

    actions = ['action_make_feature_image', 'action_make_site_image',
               'action_change_site', 'action_rotate_image']
    fields = ('feature', 'image', 'linked_thumbnail', 'status', 'photographer',
        'copyright',
        'caption', 'description', 'source_format', 'upload_file_format',
        'upload_filename', 'resolution', 'width', 'height', 'bit_depth',
        'colour_mode', 'camera_details', 'photo_date', 'editing_software',
              'editing_notes', 'order')
    list_display = ('caption', 'linked_thumbnail', 'feature', 'site', 'status',
                    'modified', 'created')
    list_filter = ['status', 'photographer', 'feature__site',
                   'feature__site__regions', ('created', CustomDateFieldListFilter), ('modified', CustomDateFieldListFilter)]
    readonly_fields = ('height', 'feature', 'linked_thumbnail', 'width')
    search_fields = ['feature__site__name', 'image']
    image_type = 'feature'

    def action_change_site (self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect('change_site/?ids=%s' % ','.join(selected))
    action_change_site.short_description = \
        'Associate selected images with a different site'

    def action_make_feature_image (self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect('make_feature_image/?ids=%s' %
                                    ','.join(selected))
    action_make_feature_image.short_description = \
        'Associate selected images with another feature'

    def action_make_site_image (self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect('make_site_image/?ids=%s' %
                                    ','.join(selected))
    action_make_site_image.short_description = \
        'Associate selected images with their site'

    def change_site (self, request):
        """View for change the site a SiteImage is associated with."""
        context = {}
        feature_image_ids = request.GET.get('ids', '')
        site = self._get_common_site(feature_image_ids)
        if not site:
            context['message'] = 'You have selected images from more than one site. Please go back and select only images associated with the same site.'
            form = sculpture.forms.admin.ChangeSiteForImageForm([])
        elif request.POST:
            site_choices = self._get_site_choices()
            form = sculpture.forms.admin.ChangeSiteForImageForm(
                site_choices, request.POST)
            if form.is_valid():
                site_id = form.cleaned_data['site']
                feature_image_ids = form.cleaned_data['image_ids'].split(',')
                for feature_image_id in feature_image_ids:
                    self._change_site(feature_image_id, site_id)
                return redirect('admin:sculpture_siteimage_changelist')
        else:
            site_choices = self._get_site_choices()
            data = {'image_ids': feature_image_ids}
            form = sculpture.forms.admin.ChangeSiteForImageForm(
                site_choices, initial=data)
        context['form'] = form
        return render(request, 'sculpture/admin/change_site_for_image.html',
                      context)

    def _change_site (self, feature_image_id, site_id):
        feature_image = sculpture.models.FeatureImage.objects.get(
            pk=feature_image_id)
        kwargs = dict([(fld.name, getattr(feature_image, fld.name)) for fld
                       in feature_image._meta.fields
                       if fld != feature_image._meta.pk])
        kwargs.pop('feature')
        site_image = sculpture.models.SiteImage(
            site_id=site_id, **kwargs)
        site_image.save()
        feature_image.delete()

    def _get_common_site (self, feature_image_ids):
        """Returns the Site that all `feature_image_ids` are associated
        with, or None."""
        site = None
        for feature_image_id in feature_image_ids.split(','):
            try:
                feature_image = sculpture.models.FeatureImage.objects.get(
                    pk=feature_image_id)
            except sculpture.models.FeatureImage.DoesNotExist:
                return None
            if site is None:
                site = feature_image.feature.site
            elif feature_image.feature.site != site:
                return None
        return site

    def get_urls (self):
        urls = super(FeatureImageAdmin, self).get_urls()
        extra_urls = [
            url(r'^change_site/$', self.admin_site.admin_view(
                self.change_site)),
            url(r'^make_feature_image/$', self.admin_site.admin_view(
                self.make_feature_image)),
            url(r'^make_site_image/$', self.admin_site.admin_view(
                self.make_site_image)),
            ]
        return extra_urls + urls

    def make_feature_image (self, request):
        """View for associating a FeatureImage with another Feature."""
        context = {}
        feature_image_ids = request.GET.get('ids', '')
        site = self._get_common_site(feature_image_ids)
        if not site:
            context['message'] = 'You have selected images from more than one site. Please go back and select only images associated with the same site.'
            form = sculpture.forms.admin.MakeFeatureImageForm([])
        elif request.POST:
            feature_choices = self._get_feature_choices(site)
            form = sculpture.forms.admin.MakeFeatureImageForm(
                feature_choices, request.POST)
            if form.is_valid():
                feature_id = form.cleaned_data['feature']
                feature_image_ids = form.cleaned_data['image_ids'].split(',')
                for feature_image_id in feature_image_ids:
                    self._make_feature_image(feature_image_id, feature_id)
                return redirect('admin:sculpture_feature_changelist')
        else:
            feature_choices = self._get_feature_choices(site)
            data = {'image_ids': feature_image_ids}
            form = sculpture.forms.admin.MakeFeatureImageForm(
                feature_choices, initial=data)
        context['form'] = form
        return render(request, 'sculpture/admin/change_feature_image.html',
                      context)

    def _make_feature_image (self, feature_image_id, feature_id):
        feature_image = sculpture.models.FeatureImage.objects.get(
            pk=feature_image_id)
        feature = sculpture.models.Feature.objects.get(pk=feature_id)
        feature_image.feature = feature
        feature_image.save()

    def make_site_image (self, request):
        """View for associating a FeatureImage with its Site."""
        context = {}
        feature_image_ids = request.GET.get('ids', '')
        site = self._get_common_site(feature_image_ids)
        if not site:
            context['message'] = 'You have selected images from more than one site. Please go back and select only images associated with the same site.'
        elif request.POST:
            form = sculpture.forms.admin.MakeSiteImageForm(request.POST)
            if form.is_valid():
                feature_image_ids = form.cleaned_data['image_ids'].split(',')
                for feature_image_id in feature_image_ids:
                    self._make_site_image(feature_image_id, site.id)
                return redirect('admin:sculpture_featureimage_changelist')
        else:
            data = {'image_ids': feature_image_ids}
            form = sculpture.forms.admin.MakeSiteImageForm(initial=data)
            context['form'] = form
        return render(request, 'sculpture/admin/make_site_image.html', context)

    def _make_site_image (self, feature_image_id, site_id):
        feature_image = sculpture.models.FeatureImage.objects.get(
            pk=feature_image_id)
        kwargs = dict([(fld.name, getattr(feature_image, fld.name)) for fld
                       in feature_image._meta.fields
                       if fld != feature_image._meta.pk])
        kwargs.pop('feature')
        site_image = sculpture.models.SiteImage(
            site_id=site_id, **kwargs)
        site_image.save()
        feature_image.delete()

    def get_queryset (self, request):
        """Returns a QuerySet of FeatureImages viewable by the request
        user."""
        qs = super(FeatureImageAdmin, self).get_queryset(request)
        return sculpture.utils.restrict_queryset_by_site_permissions(
            qs, request, 'feature__site__')

    def response_change (self, request, obj):
        response = super(FeatureImageAdmin, self).response_change(request, obj)
        if '_save' in request.POST:
            response = redirect('admin:sculpture_feature_change',
                                obj.feature.id)
        return response

    def _rotate_image (self, image_id, temp_dir):
        image = sculpture.models.FeatureImage.objects.get(pk=image_id)
        super(FeatureImageAdmin, self)._rotate_image(image, temp_dir)


class FeatureSetAdmin (admin.ModelAdmin):

    fields = ('feature_set', 'order', 'name', 'n')
    list_display = ('order', 'name', 'feature_set', 'modified', 'created')
    list_display_links = ('order', 'name', 'feature_set')


class GlossaryTermAdmin (admin.ModelAdmin):

    inlines = [GlossaryTermNameInline]
    list_display = ('name', 'broader_term', 'modified', 'created')


class PeriodAdmin (admin.ModelAdmin):

    list_display = ('name', 'modified', 'created')


class RegionAdmin (admin.ModelAdmin):

    list_display = ('name', 'modified', 'created')


class RegionTypeAdmin (admin.ModelAdmin):

    list_display = ('name', 'modified', 'created')


class SettlementAdmin (admin.ModelAdmin):

    list_display = ('name', 'modified', 'created')


class SiteAdmin (admin.ModelAdmin):

    actions = ['action_download_images', 'action_export_list',
               'action_link_glossary']
    fieldsets = [
        ('Location', {'fields': ['name', 'country', 'grid_reference',
                                 'settlement']}),
        (None, {'fields': ['site_id', 'visit_date', 'status', 'authors', 'fieldworker_may_2017']}),
        ('Description', {'fields': ['description']}),
        ('History', {'fields': ['history']}),
        ('Comments/Opinions', {'fields': ['comments']}),
        ('Notes', {'fields': ['fieldworker_notes', 'editor_notes']}),
        ]
    filter_horizontal = ['authors']
    form = sculpture.forms.admin.SiteAdminForm
    inlines = [SiteDioceseInline, SiteRegionInline, SiteDedicationInline,
               SiteImageInline, FeatureInline, BibliographyItemInline,
               ExternalSiteInline]
    list_display = ('name', 'region', 'status', 'country', 'fieldworker_may_2017',
                    'fieldworker_notes', 'editor_notes', 'settlement',
                    'modified', 'created', 'site_id')
    list_display_links = ('site_id', 'name', 'status', 'country')
    list_filter = ['status', 'authors', 'country', ('created', CustomDateFieldListFilter), ('modified', CustomDateFieldListFilter),
                   'dedications', NowDedicationListFilter, 'dioceses',
                   HasDedicationListFilter, HasDioceseListFilter,
                   HasFeatureImagesListFilter, HasGridReferenceListFilter,
                   HasTraditionalRegionListFilter, HasSettlementListFilter,
                   HasSiteImagesListFilter, MissingTextListFilter,
                   IsPosssibleDuplicateListFilter, 'regions',
                   NowRegionListFilter, Pre1974RegionListFilter, 'settlement']
    search_fields = ['name', 'country__name', 'regions__name', 'dioceses__name',
                     'dedications__name', 'settlement__name']

    def action_download_images (self, request, queryset):
        """Returns an HTTPResponse transmitting a ZIP file of images
        associated with the sites in `queryset`."""
        base = settings.IMAGE_SERVER_ROOT
        temp = tempfile.TemporaryFile(dir=base)
        archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_STORED)
        for site in queryset:
            metadata_temp = StringIO.StringIO()
            fieldnames = ['filename', 'caption', 'photographer', 'date',
                          'visit date', 'fieldworkers']
            metadata_writer = csv.DictWriter(metadata_temp, fieldnames)
            # Python 2.6 doesn't have the DictWriter.writeheader
            # method.
            metadata_writer.writerow(dict((fieldname, fieldname) for fieldname
                                          in fieldnames))
            for image in site.get_images():
                image_name = image.image.name
                archive.write(os.path.join(base, image_name),
                              os.path.join(site.site_id, image_name))
                metadata_writer.writerow(image.get_metadata())
            archive.writestr(os.path.join(site.site_id, 'metadata.csv'),
                                          metadata_temp.getvalue())
        archive.close()
        wrapper = FileWrapper(temp)
        response = HttpResponse(wrapper, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=site_images.zip'
        response['Content-Length'] = temp.tell()
        temp.seek(0)
        return response
    action_download_images.short_description = \
        'Download ZIP file of images and metadata for selected sites'

    def action_export_list (self, request, queryset):
        """Exports basic site details in CSV for each Site in `queryset`."""
        site_list = StringIO.StringIO()
        fieldnames = ['name', 'region (now)', 'country', 'fieldworkers']
        site_list_writer = csv.DictWriter(site_list, fieldnames)
        site_list_writer.writerow(dict((fieldname, fieldname) for fieldname
                                       in fieldnames))
        for site in queryset:
            fieldworkers = [author.name.encode('utf-8') for author in
                            site.authors.all()]
            site_data = {'name': site.name.encode('utf-8'),
                         'region (now)': self.region(site).encode('utf-8'),
                         'country': site.country.name.encode('utf-8'),
                         'fieldworkers': ', '.join(fieldworkers)}
            site_list_writer.writerow(site_data)
        return HttpResponse(site_list.getvalue(), content_type='text/csv')
    action_export_list.short_description = 'Export site information as CSV'

    def action_link_glossary (self, request, queryset):
        """Recreates glossary links for each Site in `queryset`."""
        for site in queryset:
            # Just save each object, since the glossary linking is
            # done within Site.save().
            site.save()
    action_link_glossary.short_description = \
        'Regenerate glossary links for selected sites'

    def bulk_image_upload (self, request, site_id):
        # Custom view for performing a bulk upload of images to become
        # SiteImages.
        site = get_object_or_404(sculpture.models.Site, pk=site_id)
        if request.method == 'POST':
            form = sculpture.forms.admin.BulkSiteImageUpload(
                request.POST, request.FILES)
            if form.is_valid():
                for image in request.FILES.getlist('image'):
                    form_data = form.cleaned_data
                    form_data.update({'image': image, 'site': site})
                    instance = sculpture.models.SiteImage(**form_data)
                    instance.save()
                return redirect('admin:sculpture_site_change', site_id)
        else:
            form = sculpture.forms.admin.BulkSiteImageUpload()
        context = {'form': form, 'add': True, 'title': 'Add SiteImages'}
        return render(request, 'sculpture/admin/bulk_image_upload.html',
                      context)

    def formfield_for_foreignkey (self, db_field, request, **kwargs):
        if db_field.name == 'status':
            kwargs['queryset'] = sculpture.models.SiteStatus.objects.filter_by_user(request.user)
        return super(SiteAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

    def get_actions (self, request):
        actions = super(SiteAdmin, self).get_actions(request)
        user = request.user
        # Only editors and superusers may recreate glossary links.
        if not (user.is_superuser or sculpture.utils.get_profile(user).is_editor):
            del actions['action_link_glossary']
        return actions

    def get_readonly_fields (self, request, obj=None):
        fields = list(super(SiteAdmin, self).get_readonly_fields(request, obj))
        # If the user is a fieldworker, make the editor's notes field
        # read-only.
        user = request.user
        if not (user.is_superuser or sculpture.utils.get_profile(user).is_editor):
            fields.append('editor_notes')
            fields.append('site_id')
        return fields

    def get_urls (self):
        urls = super(SiteAdmin, self).get_urls()
        extra_urls = [
            url(r'^(?P<site_id>\d+)/bulk_image_upload/$',
                self.admin_site.admin_view(self.bulk_image_upload))
            ]
        return extra_urls + urls

    def _mark_status (self, request, queryset, status):
        status = sculpture.models.SiteStatus.objects.get(name=status)
        rows_updated = queryset.update(status=status)
        if rows_updated == 1:
            message = '1 Site was'
        else:
            message = '%d Sites were' % rows_updated
        self.message_user(request, '%s successfully marked as %s'
                          % (message, status))

    def get_queryset (self, request):
        """Returns a QuerySet of Sites viewable by the request user."""
        qs = super(SiteAdmin, self).get_queryset(request)
        return sculpture.utils.restrict_queryset_by_site_permissions(
            qs, request)

    def region (self, site):
        return sculpture.utils.get_first_name(
            site.get_region_by_period(sculpture.constants.DATE_NOW), 'region')

    def save_model (self, request, obj, form, change):
        if not change:
            # Set the status to draft.
            draft_status = sculpture.models.SiteStatus.objects.get(
                name=sculpture.constants.SITE_STATUS_DRAFT)
            obj.status = draft_status
        else:
            # Send a signal; done here rather than as pre-/post-save
            # to allow for checking for changed values, since obj has
            # the new values but the database is not yet changed.
            sculpture.signals.site_change.send(sender=sculpture.models.Site,
                                               site=obj)
        super(SiteAdmin, self).save_model(request, obj, form, change)

    def save_related (self, request, form, formsets, change):
        super(SiteAdmin, self).save_related(request, form, formsets, change)
        if not change:
            user = request.user
            profile = sculpture.utils.get_profile(user)
            # Ensure that the person creating a new Site is listed as
            # an author of the record. This must happen after saving
            # all of the formsets, for otherwise any change made will
            # be overwritten.
            try:
                form.instance.authors.add(profile.contributor)
            except sculpture.models.Contributor.DoesNotExist:
                now = django.utils.timezone.now()
                name = '%s %s' % (user.first_name, user.last_name)
                contributor = sculpture.models.Contributor(
                    user_profile=profile, name=name.strip(), created=now,
                    modified=now)
                contributor.save()
                form.instance.authors.add(contributor)


class SiteImageAdmin (BaseImageAdmin):

    actions = ['action_make_feature_image', 'action_change_site',
               'action_rotate_image']
    fields = ('site', 'image', 'linked_thumbnail', 'status', 'photographer',
        'copyright',
        'caption', 'description', 'source_format', 'upload_file_format',
        'upload_filename', 'resolution', 'width', 'height', 'bit_depth',
        'colour_mode', 'camera_details', 'photo_date', 'editing_software',
        'editing_notes', 'order')
    list_display = ('caption', 'linked_thumbnail', 'site', 'status', 'modified',
                    'created')
    list_filter = ('status', 'site', 'photographer', 'site__regions', ('created', CustomDateFieldListFilter),
                   'modified')
    readonly_fields = ('height', 'site', 'linked_thumbnail', 'width')
    search_fields = ['site__name', 'image']
    image_type = 'site'

    def action_change_site (self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect('change_site/?ids=%s' % ','.join(selected))
    action_change_site.short_description = \
        'Associate selected images with a different site'

    def action_make_feature_image (self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect('make_feature_image/?ids=%s' %
                                    ','.join(selected))
    action_make_feature_image.short_description = \
        'Associate selected images with a feature'

    def change_site (self, request):
        """View for change the site a SiteImage is associated with."""
        context = {}
        site_image_ids = request.GET.get('ids', '')
        site = self._get_common_site(site_image_ids)
        if not site:
            context['message'] = 'You have selected images from more than one site. Please go back and select only images associated with the same site.'
            form = sculpture.forms.admin.ChangeSiteForImageForm([])
        elif request.POST:
            site_choices = self._get_site_choices()
            form = sculpture.forms.admin.ChangeSiteForImageForm(
                site_choices, request.POST)
            if form.is_valid():
                site_id = form.cleaned_data['site']
                site_image_ids = form.cleaned_data['image_ids'].split(',')
                for site_image_id in site_image_ids:
                    self._change_site(site_image_id, site_id)
                return redirect('admin:sculpture_siteimage_changelist')
        else:
            site_choices = self._get_site_choices()
            data = {'image_ids': site_image_ids}
            form = sculpture.forms.admin.ChangeSiteForImageForm(
                site_choices, initial=data)
        context['form'] = form
        return render(request, 'sculpture/admin/change_site_for_image.html',
                      context)

    def _change_site (self, site_image_id, site_id):
        site_image = sculpture.models.SiteImage.objects.get(pk=site_image_id)
        site_image.site_id = site_id
        site_image.save()

    def _get_common_site (self, site_image_ids):
        """Returns the Site that all `site_image_ids` are associated
        with, or None."""
        site = None
        for site_image_id in site_image_ids.split(','):
            try:
                site_image = sculpture.models.SiteImage.objects.get(
                    pk=site_image_id)
            except sculpture.models.SiteImage.DoesNotExist:
                return None
            if site is None:
                site = site_image.site
            elif site_image.site != site:
                return None
        return site

    def get_urls (self):
        urls = super(SiteImageAdmin, self).get_urls()
        extra_urls = [
            url(r'^change_site/$', self.admin_site.admin_view(
                self.change_site)),
            url(r'^make_feature_image/$', self.admin_site.admin_view(
                self.make_feature_image))
            ]
        return extra_urls + urls

    def make_feature_image (self, request):
        """View for converting a SiteImage into a FeatureImage."""
        context = {}
        site_image_ids = request.GET.get('ids', '')
        site = self._get_common_site(site_image_ids)
        if not site:
            context['message'] = 'You have selected images from more than one site. Please go back and select only images associated with the same site.'
            form = sculpture.forms.admin.MakeFeatureImageForm([])
        elif request.POST:
            feature_choices = self._get_feature_choices(site)
            form = sculpture.forms.admin.MakeFeatureImageForm(
                feature_choices, request.POST)
            if form.is_valid():
                feature_id = form.cleaned_data['feature']
                site_image_ids = form.cleaned_data['image_ids'].split(',')
                for site_image_id in site_image_ids:
                    self._make_feature_image(site_image_id, feature_id)
                return redirect('admin:sculpture_siteimage_changelist')
        else:
            feature_choices = self._get_feature_choices(site)
            if not feature_choices:
                context['message'] = 'The site associated with the selected images has no features to assign the images to. Create the desired feature and perform this operation again.'
            data = {'image_ids': site_image_ids}
            form = sculpture.forms.admin.MakeFeatureImageForm(
                feature_choices, initial=data)
        context['form'] = form
        return render(request, 'sculpture/admin/make_feature_image.html',
                      context)

    def _make_feature_image (self, site_image_id, feature_id):
        site_image = sculpture.models.SiteImage.objects.get(pk=site_image_id)
        kwargs = dict([(fld.name, getattr(site_image, fld.name)) for fld
                       in site_image._meta.fields
                       if fld != site_image._meta.pk])
        kwargs.pop('site')
        feature_image = sculpture.models.FeatureImage(
            feature_id=feature_id, **kwargs)
        feature_image.save()
        site_image.delete()

    def get_queryset (self, request):
        """Returns a QuerySet of SiteImages viewable by the request
        user."""
        qs = super(SiteImageAdmin, self).get_queryset(request)
        return sculpture.utils.restrict_queryset_by_site_permissions(
            qs, request, 'site__')

    def response_change (self, request, obj):
        response = super(SiteImageAdmin, self).response_change(request, obj)
        if '_save' in request.POST:
            response = redirect('admin:sculpture_site_change',
                                obj.site.id)
        return response

    def _rotate_image (self, image_id, temp_dir):
        image = sculpture.models.SiteImage.objects.get(pk=image_id)
        super(SiteImageAdmin, self)._rotate_image(image, temp_dir)


class SiteStatusAdmin (admin.ModelAdmin):

    list_display = ('name', 'modified', 'created')


class UserFeedbackAdmin (admin.ModelAdmin):

    list_display = ('page_link', 'feedback', 'created')


admin.site.register(sculpture.models.BibliographyItem, BibliographyItemAdmin)
admin.site.register(sculpture.models.Contributor, ContributorAdmin)
admin.site.register(sculpture.models.Country, CountryAdmin)
admin.site.register(sculpture.models.Dedication, DedicationAdmin)
admin.site.register(sculpture.models.Dimension, DimensionAdmin)
admin.site.register(sculpture.models.Diocese, DioceseAdmin)
admin.site.register(sculpture.models.Feature, FeatureAdmin)
admin.site.register(sculpture.models.FeatureImage, FeatureImageAdmin)
admin.site.register(sculpture.models.FeatureSet, FeatureSetAdmin)
admin.site.register(sculpture.models.GlossaryTerm, GlossaryTermAdmin)
admin.site.register(sculpture.models.ImageStatus)
admin.site.register(sculpture.models.Period, PeriodAdmin)
admin.site.register(sculpture.models.Region, RegionAdmin)
admin.site.register(sculpture.models.RegionType, RegionTypeAdmin)
admin.site.register(sculpture.models.Settlement, SettlementAdmin)
admin.site.register(sculpture.models.Site, SiteAdmin)
admin.site.register(sculpture.models.SiteImage, SiteImageAdmin)
admin.site.register(sculpture.models.SiteStatus, SiteStatusAdmin)
admin.site.register(sculpture.models.UserFeedback, UserFeedbackAdmin)

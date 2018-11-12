import re

import django.forms

from sculpture.constants import GRID_PATTERN
import sculpture.models


class BulkImageUpload (django.forms.ModelForm):

    image = django.forms.FileField(
        label='Images', widget=django.forms.ClearableFileInput(
            attrs={'multiple': 'multiple'}),
        help_text='Accepts RAW, TIFF and JPEG files')

    class Meta:
        fields = ['image', 'photographer', 'source_format',
                  'upload_file_format', 'resolution', 'bit_depth',
                  'colour_mode', 'camera_details', 'photo_date',
                  'editing_software', 'editing_notes']


class BulkFeatureImageUpload (BulkImageUpload):

    class Meta (BulkImageUpload.Meta):
        model = sculpture.models.FeatureImage
        fields = ['image', 'photographer', 'source_format',
                  'upload_file_format', 'resolution', 'bit_depth',
                  'colour_mode', 'camera_details', 'photo_date',
                  'editing_software', 'editing_notes']


class BulkSiteImageUpload (BulkImageUpload):

    class Meta (BulkImageUpload.Meta):
        model = sculpture.models.SiteImage
        fields = ['image', 'photographer', 'source_format',
                  'upload_file_format', 'resolution', 'bit_depth',
                  'colour_mode', 'camera_details', 'photo_date',
                  'editing_software', 'editing_notes']


class ChangeSiteForImageForm (django.forms.Form):

    image_ids = django.forms.CharField(widget=django.forms.HiddenInput())
    site = django.forms.ChoiceField()

    def __init__ (self, site_choices, *args, **kwargs):
        super(ChangeSiteForImageForm, self).__init__(*args, **kwargs)
        self.fields['site'].choices = site_choices


class MakeFeatureImageForm (django.forms.Form):

    image_ids = django.forms.CharField(widget=django.forms.HiddenInput())
    feature = django.forms.ChoiceField()

    def __init__ (self, feature_choices, *args, **kwargs):
        super(MakeFeatureImageForm, self).__init__(*args, **kwargs)
        self.fields['feature'].choices = feature_choices


class MakeSiteImageForm (django.forms.Form):

    image_ids = django.forms.CharField(widget=django.forms.HiddenInput())


class RotateImageForm (django.forms.Form):

    image_ids = django.forms.CharField(widget=django.forms.HiddenInput())


class SiteAdminForm (django.forms.ModelForm):

    class Meta:
        model = sculpture.models.Site
        fields = '__all__'

    def clean_grid_reference (self):
        grid_reference = self.cleaned_data['grid_reference'].strip()
        if grid_reference:
            match = re.search(GRID_PATTERN, grid_reference)
            if match is None:
                raise django.forms.ValidationError(
                    'Grid reference is not in a valid format; check the formatting')
            else:
                # CHeck that we have the same number of digits in each
                # group.
                if match.group('bng'):
                    first = 3
                    second = 4
                else:
                    first = 7
                    second = 8
                if len(match.group(first)) != len(match.group(second)):
                    raise django.forms.ValidationError(
                        'Grid reference must have the same number of digits in each group')
        return grid_reference

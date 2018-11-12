import django.forms

import sculpture.models


class SiteTagForm (django.forms.ModelForm):

    class Meta:
        model = sculpture.models.SiteTag
        fields = '__all__'

    def clean (self):
        # Because the user field is not included in the form
        # (editable=False), the unique_together constraint that
        # includes it is not checked. Therefore recreate it here.
        cleaned_data = self.cleaned_data
        try:
            sculpture.models.SiteTag.objects.get(user=self.instance.user,
                                                 tag=cleaned_data['tag'])
        except sculpture.models.SiteTag.DoesNotExist:
            pass
        else:
            if self.cleaned_data['tag'] != self.instance.tag:
                message = 'You already have a tag with this name'
                self._errors['tag'] = self.error_class([message])
        return cleaned_data

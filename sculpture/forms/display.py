import django.forms

import sculpture.models


class SiteCommentForm (django.forms.ModelForm):

    class Meta:
        model = sculpture.models.SiteComment
        fields = '__all__'


class UserFeedbackForm (django.forms.ModelForm):

    class Meta:
        model = sculpture.models.UserFeedback
        widgets = {'page': django.forms.widgets.HiddenInput()}
        fields = '__all__'

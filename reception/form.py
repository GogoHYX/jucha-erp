from django import forms
from .models import *
from .utils import *
from django.core.validators import RegexValidator


class CheckInForm(forms.Form):
    maids = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, queryset=available_maids())
    place = forms.ChoiceField(widget=forms.RadioSelect, choices=available_places)


class ServesChange(forms.Form):
    maids_in = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                              queryset=available_maids(), required=False)
    maids_out = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                               queryset=ServesPlaces.objects, required=False)
    place = forms.ChoiceField(widget=forms.RadioSelect, choices=available_places, required=False)

    def __init__(self, *args, **kwargs):
        serves_id = kwargs.pop('serves_id', ())
        super().__init__(*args, **kwargs)
        serves = Serves.objects.get(pk=serves_id)
        self.fields['maids_out'].queryset = serves.servesmaids_set


class ManualForm(forms.ModelForm):
    customer = forms.CharField(max_length=11, required=False,
                               validators=[RegexValidator(regex='^[0-9]{11}$',
                                                          message='请输入正确的11位手机号', code='nomatch')], )

    class Meta:
        model = ServesCharge
        fields = ['manual', 'note']


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Income
        exclude = ['bill']

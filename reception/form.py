from django import forms
from .models import *
from .utils import *
from django.core.validators import RegexValidator


class CheckInForm(forms.Form):
    maids = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=available_maids)
    places = forms.ChoiceField(widget=forms.RadioSelect, choices=available_places)
    #customer = forms.CharField(max_length=11, required=False,
    #                           validators=[RegexValidator(regex='^[0-9]{11}$',
    #                                                      message='请输入正确的11位手机号', code='nomatch')], )

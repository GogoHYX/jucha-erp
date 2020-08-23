from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
# Create your views here.
from django.utils.timezone import now
from django.template import loader
from django.urls import reverse
from django.views import generic

from .models import *
from .form import *
from .utils import *

# Create your views here.


def dashboard(request):
    template = loader.get_template('reception/dashboard.html')
    maids = ('a', 'b', 'c')
    places = ('d', 'e', 'f')
    context = {

    }
    return HttpResponse(template.render(context, request))


def check_in(request):
    if request.method == 'POST':
        form = CheckInForm(data=request.POST)
        if form.is_valid():
            print(form.cleaned_data['maids'])
            print(form.cleaned_data['places'])
            return HttpResponseRedirect('/reception/dashboard/')
    template = loader.get_template('reception/check-in.html')
    form = CheckInForm()
    context = {
        'form': form,
    }
    return HttpResponse(template.render(context, request))

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.generic.edit import UpdateView, CreateView
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
            print(form.cleaned_data['place'])
            start_serves(form.cleaned_data)
            return HttpResponseRedirect(reverse('reception:dashboard'))
    template = loader.get_template('reception/check-in.html')
    form = CheckInForm()
    context = {
        'form': form,
    }
    return HttpResponse(template.render(context, request))


def ongoing_serves(request):
    template = loader.get_template('reception/ongoing-serves.html')
    context = {
        'serves_list': Serves.objects.filter(active=True)
    }
    HttpResponse(template.render(context, request))


def serves_detail(request, serves_id):
    serves = get_object_or_404(Serves, pk=serves_id)
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('serves_detail', args=[serves_id]))
    context = expense_detail(serves_id)
    template = loader.get_template('reception/serves-detail.html')
    return HttpResponse(template.render(context, request))


class ServesMaidUpdate(UpdateView):
    model = ServesMaids
    fields = ['maid', 'start', 'end']
    pass


def serves_change(request, serves_id):
    if request.method == 'POST':
        sc = ServesChange(serves_id=serves_id, data=request.POST)
        print(sc.is_valid())
        data = sc.cleaned_data
        print(data)
        data['time'] = timezone.now()
        data['serves_id'] = serves_id
        change_status(data)
        return HttpResponseRedirect(reverse('reception:dashboard'))
    form = ServesChange(serves_id=serves_id)
    template = loader.get_template('reception/serves-change.html')
    context = {
        'serves_id': serves_id,
        'form': form,
    }
    return HttpResponse(template.render(context, request))


def change_maid(request, serves_id):
    if request.method == 'POST':
        sc = ServesMaidChange(request.POST, instance=serves_id)
        print(sc.is_valid())
        data = sc.cleaned_data
        data['time'] = timezone.now()
        data['serves_id'] = serves_id
        change_maid_status(data)
        return HttpResponseRedirect(reverse('reception:dashboard'))
    form = ServesMaidChange(serves_id=serves_id)
    template = loader.get_template('reception/serves-change.html')
    context = {
        'form': form
    }
    return HttpResponse(template.render(context, request))




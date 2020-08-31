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
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('serves_detail', args=[serves_id]))
    context = expense_detail(serves_id)
    print(context)
    template = loader.get_template('reception/serves-detail.html')
    return HttpResponse(template.render(context, request))


def serves_change(request, serves_id):
    if request.method == 'POST':
        sc = ServesChange(serves_id=serves_id, data=request.POST)
        print(sc.is_valid())
        data = sc.cleaned_data
        print(data)
        data['time'] = timezone.now()
        data['serves_id'] = serves_id
        change_status(data)
        return HttpResponseRedirect(reverse('reception:serves_detail', serves_id))
    form = ServesChange(serves_id=serves_id)
    template = loader.get_template('reception/serves-change.html')
    context = {
        'serves_id': serves_id,
        'form': form,
    }
    return HttpResponse(template.render(context, request))


def check_out(request, serves_id):
    if request.Method == 'POST':
        mf = ManualForm(request.POST)
        if not mf.is_valid():
            return HttpResponseRedirect(reverse('reception:check_out', serves_id))
        serves = Serves.objects.get(pk=serves_id)
        serves.end_serves()
        context = expense_detail(serves_id)
        bill = Bill()
        if mf.cleaned_data['customer']:
            bill.customer = mf.cleaned_data['customer']
        bill.save()
        charge = mf.save(commit=False)
        charge.total = context['total']
        charge.bill = bill
        charge.serves = serves
        charge.save()
        return HttpResponseRedirect(reverse('pay', bill.id))

    context = expense_detail(serves_id, update=False)
    form = ManualForm
    print(context)
    context['form'] = form
    template = loader.get_template('reception/check-out.html')
    return HttpResponse(template.render(context, request))


def pay(request, bill_id):
    if request.method == 'POST':
        pass
    template = loader.get_template('reception/pay.html')
    bill = Bill.objects.get(pk=bill_id)
    manual = 0
    if bill.servescharge:
        is_serves = True
        charge = bill.servescharge
        unpaid = check_balance(charge)
        manual = charge.manual
        back_id = charge.serves.id
    else:
        is_serves = False
        charge = bill.depositcharge
        unpaid = check_balance(charge, is_serves=False)
        back_id = 0
    incomes = bill.income_set.all()
    paid = charge.total - unpaid
    cleared = unpaid <= 0
    context = {
        'is_serves': is_serves,
        'back_id': back_id,
        'bill': bill,
        'paid': paid,
        'total': charge.total + manual,
        'unpaid': max(0, unpaid),
        'cleared': cleared,
        'incomes': incomes,
    }
    return HttpResponse(template.render(context, request))


def add_payment(request, bill_id):
    if request.method == 'POST':
        pf = PaymentForm(request.POST)
        if not pf.is_valid():
            return HttpResponseRedirect(reverse('reception:add_payment', bill_id))
        income = pf.save(commit=False)
        income.bill_id = bill_id
        income.save()
        return HttpResponseRedirect(reverse('reception:pay', bill_id))
    template = loader.get_template('reception/add-payment.html')
    bill = Bill.objects.get(pk=bill_id)
    form = PaymentForm()
    context = {
        'bill': bill,
        'form': form,
    }
    return HttpResponse(template.render(context, request))




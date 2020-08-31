from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.generic.edit import UpdateView, CreateView
from django.db.models.query import EmptyQuerySet
# Create your views here.
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
    form = CheckInForm()
    return render(request, 'reception/check-in.html', {'form': form})


def ongoing_serves(request):
    context = {
        'serves_list': Serves.objects.filter(active=True)
    }
    return render(request, 'reception/ongoing-serves.html', context)


def serves_detail(request, serves_id):
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('serves_detail', args=[serves_id]))
    context = expense_detail(serves_id)
    print(context)
    return render(request, 'reception/serves-detail.html', context)


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
    context = {
        'serves_id': serves_id,
        'form': form,
    }
    return render(request, 'reception/serves-change.html', context)


def add_item(request, serves_id):
    if request.method == 'POST':
        af = AddItemForm(request.POST)
        if af.is_valid():
            serves_item = af.save(commit=False)
            serves_item.price = serves_item.item.price
            serves_item.serves_id = serves_id
            serves_item.save()
            return HttpResponseRedirect(reverse('reception:serves_detail', serves_id))
    form = AddItemForm()
    context = {
        'serves_id': serves_id,
        'form': form,
    }
    return render(request, 'reception/add-item.html', context)


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
    return render(request, 'reception', context)


def pay(request, bill_id):
    bill = Bill.objects.get(pk=bill_id)
    logged_in = False
    have_voucher = False
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if not form.is_valid():
            failure(request, bill_id, '手机号不正确')
        customer = form.save()
        bill.customer = customer
        bill.save()
        logged_in = True
        have_voucher = not isinstance(customer.voucher_set.filter(used=False), EmptyQuerySet)
    manual = 0
    if bill.servescharge:
        is_serves = True
        charge = bill.servescharge
        unpaid = charge.unpaid_amount()
        manual = charge.manual
        back_id = charge.serves.id
    else:
        is_serves = False
        charge = bill.depositcharge
        unpaid = charge.unpaid_amount()
        back_id = bill.customer_id
    incomes = bill.income_set.all()
    paid = charge.total - unpaid
    cleared = unpaid <= 0
    context = {
        'can_use_deposit': bill.can_use_deposit(),
        'is_serves': is_serves,
        'back_id': back_id,
        'bill': bill,
        'paid': paid,
        'total': charge.total + manual,
        'unpaid': max(0, unpaid),
        'cleared': cleared,
        'incomes': incomes,
        'form': form,
        'logged_in': logged_in,
        'have_voucher': have_voucher,
    }
    return render(request, 'reception/pay.html', context)


def add_payment(request, bill_id):
    if request.method == 'POST':
        pf = PaymentForm(request.POST)
        if not pf.is_valid():
            failure(request, '请输入正确数额', bill_id)
        income = pf.save(commit=False)
        income.bill_id = bill_id
        income.save()
        return HttpResponseRedirect(reverse('reception:pay', bill_id))
    bill = Bill.objects.get(pk=bill_id)
    form = PaymentForm()
    context = {
        'bill': bill,
        'form': form,
    }
    return render(request, 'reception/add-payment.html', context)


def use_voucher(request, bill_id):
    bill = Bill.objects.get(pk=bill_id)
    if request.method == 'POST':
        form = UseVoucherForm(request.POST)
        if form.is_valid():
            v = form.cleaned_data['voucher']
            v.used = True
            v.save()
            bill.voucher = v
            bill.save()
        return HttpResponseRedirect(reverse('reception:pay', bill_id))
    form = UseVoucherForm()
    return render(request, 'reception/use-voucher.html', {'form': form })


def use_meituan(request, bill_id):
    bill = Bill.objects.get(pk=bill_id)
    if request.method == 'POST':
        form = UseMeituanForm(request.POST)
        if form.is_valid():
            v = form.save(commit=False)
            v.used = True
            if bill.customer:
                v.customer = bill.customer
            v.save()
            bill.voucher = v
            bill.save()
        return HttpResponseRedirect(reverse('reception:pay', bill_id))
    form = UseMeituanForm()
    return render(request, 'reception/use-voucher.html', {'form': form})


def use_deposit(request, bill_id):
    bill = Bill.objects.get(pk=bill_id)
    if request.method == 'POST':
        dp = DepositPaymentForm(request.POST)
        if not dp.is_valid():
            failure(request, '请输入正确数额', bill_id)
        if dp.cleaned_data['amount'] > bill.customer.card.deposit:
            failure(request, '余额不足', bill_id)

        deposit_payment = dp.save(commit=False)
        deposit_payment.bill = bill
        card = bill.customer.card
        deposit_payment.card = card
        card.deposit = card.deposit - dp.cleaned_data['amount']
        card.save()
        deposit_payment.save()
        bill.save()
        return HttpResponseRedirect(reverse('reception:pay', bill_id))
    form = DepositPaymentForm()
    context = {
        'deposit': bill.customer.card.deposit,
        'form': form,
    }
    return render(request, 'reception/add-payment.html', context)


def done(request, bill_id):
    bill = Bill.objects.get(pk=bill_id)
    if bill.customer:
        i = bill.valid_income()
        bill.customer.credit += i
        bill.customer.save()
        if bill.customer.card:
            card = bill.customer.card
            card.deposit += i * CASH_BACK_PERCENTAGE
            card.save()
    return render(request, 'reception/done.html')


def failure(request, bill_id, message):
    return render(request, 'reception/failure.html', {
        'bill_id': request.POST.charge_id,
        'message': request.POST.message,
    })



from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.urls import reverse
from decimal import Decimal

from .form import *
from .utils import *

# Create your views here.


def dashboard(request):
    context = {
        'serves_list': Serves.objects.filter(active=True),
        'available_maids': available_maids(),
        'available_places': Place.objects.filter(available=True),
        'user': request.user,
    }
    return render(request, 'reception/dashboard.html', context)


@login_required
@permission_required('reception.check_in_serves')
def check_in(request):
    if request.method == 'POST':
        form = CheckInForm(data=request.POST)
        if form.is_valid():
            start_serves(form.cleaned_data)
            return HttpResponseRedirect(reverse('reception:dashboard'))
    form = CheckInForm()
    return render(request, 'reception/check-in.html', {'form': form})


@login_required
def ongoing(request):
    context = {
        'serves_list': Serves.objects.filter(active=True),
        'ongoing_serves_charge': ServesCharge.objects.filter(paid=False),
        'ongoing_deposit_charge': DepositCharge.objects.filter(paid=False),
    }
    return render(request, 'reception/ongoing.html', context)


@login_required
def serves_detail(request, serves_id):
    if request.method == 'POST':
        return HttpResponseRedirect(reverse('serves_detail', args=[serves_id]))
    context = expense_detail(serves_id)
    context['serves'] = Serves.objects.get(pk=serves_id)
    return render(request, 'reception/serves-detail.html', context)


@login_required
@permission_required('reception.change_serves_status')
def serves_change(request, serves_id):
    if request.method == 'POST':
        sc = ServesChange(serves_id=serves_id, data=request.POST)
        if sc.is_valid():
            data = sc.cleaned_data
            if data['time'] is None:
                data['time'] = timezone.now()
            data['serves_id'] = serves_id
            success = change_status(data)
            print(success)
            return HttpResponseRedirect(reverse('reception:serves_detail', args=[serves_id]))
        else:
            return redirect(dashboard)
    form = ServesChange(serves_id=serves_id)
    context = {
        'serves_id': serves_id,
        'form': form,
    }
    return render(request, 'reception/serves-change.html', context)


@login_required
@permission_required('reception.change_serves_status')
def add_item(request, serves_id):
    if request.method == 'POST':
        af = AddItemForm(request.POST)
        if af.is_valid():
            serves_item = af.save(commit=False)
            serves_item.price = serves_item.item.price
            serves_item.serves_id = serves_id
            serves_item.save()
            return HttpResponseRedirect(reverse('reception:serves_detail', args=[serves_id]))
    form = AddItemForm()
    context = {
        'serves_id': serves_id,
        'form': form,
    }
    return render(request, 'reception/add-item.html', context)


@login_required
@permission_required('reception.check_out_serves')
def check_out(request, serves_id):
    if request.method == 'POST':
        mf = ManualForm(request.POST)
        if not mf.is_valid():
            return HttpResponseRedirect(reverse('reception:check_out', serves_id))
        serves = Serves.objects.get(pk=serves_id)

        context = expense_detail(serves_id)
        bill = Bill()
        if mf.cleaned_data['customer']:
            try:
                bill.customer = Customer.objects.get(phone=mf.cleaned_data['customer'])
            except ObjectDoesNotExist:
                customer = Customer(phone=mf.cleaned_data['customer'])
                customer.save()
                new_customer(customer)
                bill.customer = customer
        bill.save()
        charge = mf.save(commit=False)
        charge.total = context['total']
        charge.bill = bill
        charge.serves = serves
        charge.save()
        serves.end_serves()
        return HttpResponseRedirect(reverse('reception:pay', args=[bill.id]))

    context = expense_detail(serves_id, update=False)
    form = ManualForm
    context['form'] = form
    context['serves_id'] = serves_id
    return render(request, 'reception/check-out.html', context)


@login_required
@permission_required('reception.receive_money')
def pay(request, bill_id):
    bill = Bill.objects.get(pk=bill_id)
    logged_in = False
    have_voucher = False
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if not form.is_valid():
            try:
                customer = Customer.objects.get(phone=form.data['phone'])
            except ObjectDoesNotExist:
                return failure(request, bill_id, '手机号不正确')
        else:
            customer = form.save()
            new_customer(customer)
        bill.customer = customer
        bill.save()
    if bill.customer:
        logged_in = True
        if bill.customer.voucher_set.filter(used=False):
            have_voucher = True
    manual = 0
    if hasattr(bill, 'servescharge'):
        is_serves = True
        charge = bill.servescharge
        unpaid = charge.unpaid_amount()
        manual = charge.manual
        back_id = charge.serves.id
    elif hasattr(bill, 'depositcharge'):
        is_serves = False
        charge = bill.depositcharge
        unpaid = charge.unpaid_amount()
        back_id = bill.customer_id
    else:
        raise Exception
    incomes = bill.income_set.all()
    paid = charge.total + manual - unpaid
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
        'form': form,
        'logged_in': logged_in,
        'have_voucher': have_voucher,
    }
    return render(request, 'reception/pay.html', context)


@login_required
@permission_required('reception.receive_money')
def add_payment(request, bill_id):
    if request.method == 'POST':
        pf = PaymentForm(request.POST)
        if not pf.is_valid():
            return failure(request, bill_id, '未知失败')
        income = pf.save(commit=False)
        income.bill_id = bill_id
        income.receiver = request.user
        income.save()
        return HttpResponseRedirect(reverse('reception:pay', args=[bill_id]))
    bill = Bill.objects.get(pk=bill_id)
    form = PaymentForm(unpaid=request.GET.get('unpaid'))
    context = {
        'bill': bill,
        'form': form,
    }
    return render(request, 'reception/add-payment.html', context)


@login_required
@permission_required('reception.receive_money')
def use_voucher(request, bill_id):
    bill = Bill.objects.get(pk=bill_id)
    if request.method == 'POST':
        form = UseVoucherForm(data=request.POST, customer=bill.customer_id)
        if form.is_valid():
            v = form.cleaned_data['voucher']
            bill.voucher = v
            bill.save()
        return HttpResponseRedirect(reverse('reception:pay', args=[bill_id]))
    form = UseVoucherForm(customer=bill.customer_id)
    return render(request, 'reception/use-voucher.html', {'form': form, 'bill': bill})


@login_required
def use_meituan(request, bill_id):
    bill = Bill.objects.get(pk=bill_id)
    if request.method == 'POST':
        form = UseMeituanForm(request.POST)
        if form.is_valid():
            v = form.save(commit=False)
        else:
            try:
                v = Voucher.objects.get(swift_number=request.POST['swift_number'])
                if v.used:
                    return failure(request, bill_id, '已使用过')
            except ObjectDoesNotExist:
                return failure(request, bill_id, '未知错误')
        if bill.customer:
            v.customer = bill.customer
        v.save()
        bill.voucher = v
        bill.save()
        return HttpResponseRedirect(reverse('reception:pay', args=[bill_id]))
    form = UseMeituanForm()
    return render(request, 'reception/use-voucher.html', {'form': form, 'bill': bill})


@login_required
@permission_required('reception.receive_money')
def use_deposit(request, bill_id):
    bill = Bill.objects.get(pk=bill_id)
    if request.method == 'POST':
        dp = DepositPaymentForm(data=request.POST, bill_id=bill_id)
        if not dp.is_valid():
            return failure(request, bill_id, '请输入正确数额')
        if dp.cleaned_data['amount'] > bill.customer.card.deposit:
            return failure(request, bill_id, '余额不足')

        deposit_payment = dp.save(commit=False)
        deposit_payment.bill = bill
        card = bill.customer.card
        deposit_payment.card = card
        card.deposit = card.deposit - dp.cleaned_data['amount']
        card.save()
        deposit_payment.save()
        bill.save()
        return HttpResponseRedirect(reverse('reception:pay', args=[bill_id]))
    form = DepositPaymentForm(bill_id=bill_id)
    context = {
        'bill': bill,
        'deposit': True,
        'form': form,
    }
    return render(request, 'reception/add-payment.html', context)


def done(request, bill_id):
    bill = Bill.objects.get(pk=bill_id)
    if bill.voucher:
        bill.voucher.used = True
        bill.voucher.save()
    if bill.customer:
        i = bill.valid_income()
        bill.customer.credit += i
        bill.customer.save()
        if hasattr(bill, 'servescharge'):
            bill.servescharge.paid = True
            bill.servescharge.save()
            if bill.customer.card:
                card = bill.customer.card
                card.deposit += Decimal.from_float(float(i) * CASH_BACK_PERCENTAGE)
                card.save()
        else:
            charge = bill.depositcharge
            charge.paid = True
            charge.save()
            if hasattr(bill.customer, 'card'):
                card = bill.customer.card
                card.deposit += charge.deposit_amount
            else:
                card = Card(deposit=charge.deposit_amount, customer=bill.customer)
            card.save()
    return render(request, 'reception/done.html', {'bill': bill})


@login_required
def failure(request, bill_id, message):
    return render(request, 'reception/failure.html', {
        'bill_id': bill_id,
        'message': message,
    })


@login_required
@permission_required('reception.receive_money')
def create_card(request, customer_id):
    customer = Customer.objects.get(pk=customer_id)
    if request.method == 'POST':
        card_form = DepositChargeForm(request.POST)
        if card_form.is_valid():
            dc = card_form.save(commit=False)
            bill = Bill()
            bill.customer = customer
            bill.save()
            dc.bill = bill
            dc.save()
            return HttpResponseRedirect(reverse('reception:pay', args=[bill.id]))
        else:
            return HttpResponseRedirect(reverse('reception:create_card'), args=[customer_id])
    form = DepositChargeForm()
    return render(request, 'reception/create-card.html', {
        'form': form,
        'customer': customer,
    })


@login_required
def customer_detail(request):
    customer = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if not form.is_valid():
            try:
                customer = Customer.objects.get(phone=form.data['phone'])
            except ObjectDoesNotExist:
                return redirect(dashboard)
        else:
            customer = form.save()
            new_customer(customer)
    if request.method == 'GET' and request.GET.get('cid') is not None:
        try:
            customer = Customer.objects.get(pk=request.GET.get('cid'))
        except ObjectDoesNotExist:
            return redirect(dashboard)
    form = LoginForm()
    context = {
        'form': form,
        'customer': customer,
        'ongoing_serves': Serves.objects.filter(active=True, servescharge__bill__customer=customer),
        'past_serves': Serves.objects.filter(active=False, servescharge__bill__customer=customer),
        'ongoing_serves_charge': ServesCharge.objects.filter(paid=False, bill__customer=customer),
        'past_serves_charge': ServesCharge.objects.filter(paid=True, bill__customer=customer),
        'ongoing_deposit_charge': DepositCharge.objects.filter(paid=False, bill__customer=customer),
        'past_deposit_charge': DepositCharge.objects.filter(paid=True, bill__customer=customer),
    }
    return render(request, 'reception/customer-detail.html', context)


def login(request):
    if request.method == "GET":
        form = UserLoginForm()
        return render(request, "reception/login.html", {'form': form})
    username = request.POST.get("username")
    password = request.POST.get("password")
    user_obj = auth.authenticate(username=username, password=password)
    if not user_obj:
        return redirect(login)
    else:
        print(user_obj.username)
        auth.login(request, user_obj)
        return redirect(dashboard)


@login_required
def logout(request):
    auth.logout(request)
    return redirect(dashboard)


def register(request):
    if request.method == 'GET':
        return render(request, 'reception/register.html')
    if request.method == 'POST':
        name = request.POST.get('username')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        try:
            customer = Customer.objects.get(phone=phone)
        except ObjectDoesNotExist:
            customer = Customer(phone=phone)
        user = User.objects.create_user(username=name, password=password)
        customer.user = user
        customer.save()
        return redirect(login)


@login_required
@permission_required('manage')
def manage(request):
    pass


@login_required
@permission_required('receive_money')
def credit_redeem(request, customer_id):
    if request.method == 'POST':
        af = CreditRedeemForm(request.POST)
        if af.is_valid():
            ct = af.save(commit=False)
            ct.credit = ct.item.price
            ct.customer_id = customer_id
            ct.save()
            return HttpResponseRedirect(reverse('reception:customer_detail') + '?customer_id=%s' % customer_id)
    form = CreditRedeemForm
    context = {
        'serves_id': customer_id,
        'form': form,
    }
    return render(request, 'reception/add-item.html', context)

@login_required
@permission_required('manage')
def set_schedule(request):
    if request.method == 'POST':
        form = ScheduleExcelForm(request.POST, request.FILES)
        if form.is_valid():
            handle_schedule_xlxs(request.FILES['file'])
            return redirect(dashboard)
    else:
        form = ScheduleExcelForm()
    return render(request, 'reception/set-schedule.html', {'form': form})


def clock_in_out(request):
    pass

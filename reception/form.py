from django import forms
from .utils import *
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class CheckInForm(forms.Form):
    maids = forms.ModelMultipleChoiceField(label='女仆', widget=forms.CheckboxSelectMultiple, queryset=available_maids())
    place = forms.ChoiceField(label='场地', widget=forms.RadioSelect, choices=available_places)


class ServesChange(forms.Form):
    time = forms.DateTimeField(label='改动时间', initial=timezone.now())

    maids_in = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, label='新增女仆',
                                              queryset=available_maids(), required=False)
    maids_out = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple, label='退出女仆',
                                               queryset=Maid.objects.none(), required=False)
    place = forms.ChoiceField(label='新场地', widget=forms.RadioSelect, choices=available_places, required=False)

    def __init__(self, *args, **kwargs):
        serves_id = kwargs.pop('serves_id', ())
        super().__init__(*args, **kwargs)
        serves = Serves.objects.get(pk=serves_id)
        self.fields['maids_out'].queryset = serves.servesmaids_set.filter(active=True)


class ManualForm(forms.ModelForm):
    customer = forms.CharField(max_length=11, required=False, label='客户手机',
                               validators=[RegexValidator(regex='^[0-9]{11}$',
                                                          message='请输入正确的11位手机号', code='nomatch')], )

    class Meta:
        model = ServesCharge
        fields = ['manual', 'note']


class PaymentForm(forms.ModelForm):

    class Meta:
        model = Income
        exclude = ['bill', 'receiver']

    def __init__(self, *args, **kwargs):
        unpaid = kwargs.pop('unpaid', 0)
        super().__init__(*args, **kwargs)
        self.fields['amount'].initial = unpaid


class DepositPaymentForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        bill_id = kwargs.pop('bill_id', ())
        super().__init__(*args, **kwargs)
        bill = Bill.objects.get(pk=bill_id)
        deposit_amount = bill.customer.card.deposit
        self.fields['amount'].initial = min(bill.servescharge.unpaid_amount(), deposit_amount)

    class Meta:
        model = DepositPayment
        exclude = ['bill', 'card']


class UseVoucherForm(forms.Form):
    voucher = forms.ModelChoiceField(widget=forms.RadioSelect, label='使用代金券',
                                             queryset=Voucher.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        cid = kwargs.pop('customer', ())
        super().__init__(*args, **kwargs)
        c = Customer.objects.get(pk=cid)
        self.fields['voucher'].queryset = c.voucher_set.all()


class UseMeituanForm(forms.ModelForm):
    class Meta:
        model = Voucher
        exclude = ['used', 'customer']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type'].queryset = VoucherType.objects.filter(meituan=True)


class LoginForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['phone']
        labels = {
            'phone': '客户手机号'
        }


class AddItemForm(forms.ModelForm):
    class Meta:
        model = ServesItems
        exclude = ['serves', 'price']
        widgets = {
            'item': forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item'].queryset = Menu.objects.filter(active=True)


class DepositChargeForm(forms.ModelForm):
    class Meta:
        model = DepositCharge
        exclude = ['bill', 'paid']


class UserLoginForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label='密码')

    class Meta:
        model = User
        fields = ['username', 'password']
        labels = {
            'username': '用户名',
        }
        help_texts = {
            'username': ''
        }


class CreditRedeemForm(forms.ModelForm):
    class Meta:
        model = CreditTransaction
        exclude = ['customer', 'credit']
        widgets = {
            'item': forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item'].queryset = CreditMenu.objects.filter(active=True)
from django.db import models
from django.utils.timezone import now, get_current_timezone
from django.core.validators import RegexValidator
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import auth
from django.contrib.auth.models import User


MAID_PRICE = 90
CASH_BACK_PERCENTAGE = 0.1


# Create your models here.
class Maid(models.Model):
    identity = models.CharField('身份证号', max_length=18,
                                validators=[RegexValidator(regex='^[0-9]{17}[0-9X]$',
                                                           message='请输入正确的身份证号，包含数字和大写X', code='nomatch')],
                                unique=True)
    name = models.CharField('姓名', max_length=5, )
    cos_name = models.CharField('昵称', max_length=5, unique=True)
    wechat_id = models.CharField('微信号', max_length=40, unique=True)
    phone = models.CharField('手机号', max_length=11,
                             validators=[RegexValidator(regex='^[0-9]{11}$',
                                                        message='请输入正确的11位手机号', code='nomatch')],
                             unique=True)

    available = models.BooleanField('空闲', default=False)
    active = models.BooleanField('在职', default=True)
    fulltime = models.BooleanField('全职', default=False)
    price = models.PositiveSmallIntegerField('价格', default=MAID_PRICE)
    user = models.OneToOneField(User, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.cos_name

    class Meta:
        ordering = ['name']
        verbose_name = "女仆"
        verbose_name_plural = verbose_name


class MaidSchedule(models.Model):
    maid = models.ForeignKey(Maid, on_delete=models.PROTECT)
    date = models.DateField()
    start = models.TimeField('上班')
    end = models.TimeField('下班')

    class Meta:
        ordering = ['date']
        verbose_name = "女仆排班"
        verbose_name_plural = verbose_name
        permissions = [
            ("set_schedule", "可以给女仆排班"),
        ]


class Customer(models.Model):
    wechat_id = models.CharField('微信号', max_length=40, blank=True, null=True)
    name = models.CharField('姓名', max_length=20, blank=True, null=True)
    phone = models.CharField('手机号', max_length=11,
                             validators=[RegexValidator(regex='^[0-9]{11}$',
                                                        message='请输入正确的11位手机号', code='nomatch')],
                             unique=True, )
    GENDER_CHOICE = ((u'M', u'男'), (u'F', u'女'),)
    gender = models.CharField(max_length=2, choices=GENDER_CHOICE, blank=True, null=True)
    credit = models.IntegerField('积分', default=0)
    user = models.OneToOneField(User, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.phone

    class Meta:
        verbose_name = "顾客"
        verbose_name_plural = verbose_name


class Privilege(models.Model):
    name = models.CharField('名称', max_length=40, unique=True)
    note = models.CharField('备注', max_length=200)

    def __str__(self):
        return self.name


class Card(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.PROTECT)
    number = models.CharField('会员卡号', max_length=20, unique=True, blank=True, null=True)
    deposit = models.DecimalField('余额', max_digits=8, decimal_places=2)
    privilege = models.ManyToManyField(Privilege, blank=True)

    def __str__(self):
        return '客户: ' + self.customer.phone + ' 余额：' + str(self.deposit)


    class Meta:
        verbose_name = '储值卡'
        verbose_name_plural = verbose_name
        permissions = [
            ("add_reservation", "Can add a new reservation"),
            ("close_reservation", "Can close a reservation"),
        ]


class Place(models.Model):
    name = models.CharField('名称', max_length=10, unique=True)
    price = models.PositiveSmallIntegerField('每小时价格')
    available = models.BooleanField('空闲', default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "场地"
        verbose_name_plural = verbose_name


class Menu(models.Model):
    item = models.CharField('项目', max_length=20, unique=True)
    price = models.PositiveSmallIntegerField('单价')
    active = models.BooleanField('仍在提供')

    def __str__(self):
        return self.item

    class Meta:
        ordering = ['item']
        verbose_name = "价目表"
        verbose_name_plural = verbose_name


class Reserve(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    time = models.DateTimeField('开始时间', default=now)
    maid_NO = models.PositiveSmallIntegerField('女仆数', default=1)
    maid = models.ManyToManyField(Maid, blank=True)
    place = models.ForeignKey(Place, blank=True, null=True, on_delete=models.PROTECT)
    active = models.BooleanField('有效', default=True)
    THROUGH_CHOICE = (('MP', '小程序'), ('WC', '微信'), ('PH', '电话'), ('MA', '女仆'))
    advanced_payment = models.SmallIntegerField('定金')
    through = models.CharField('途径', choices=THROUGH_CHOICE, max_length=2)

    def __str__(self):
        pass

    class Meta:
        verbose_name = "预约"
        verbose_name_plural = verbose_name
        permissions = [
            ("add_reservation", "Can add a new reservation"),
            ("close_reservation", "Can close a reservation"),
        ]


class Serves(models.Model):
    place = models.ManyToManyField(Place, through='ServesPlaces')
    start = models.DateTimeField('开始时间', default=now)
    end = models.DateTimeField('结束时间', default=now)
    item = models.ManyToManyField(Menu, through='ServesItems')
    maid = models.ManyToManyField(Maid, through='ServesMaids')
    active = models.BooleanField('进行中', default=True)

    def __str__(self):
        maids = self.maid.all().distinct()
        place = self.servesplaces_set.order_by('-end')[0]
        return '开始时间：' + show_time(self.start) + '\n女仆： ' + \
               ' '.join([str(m) for m in maids]) + '\n场地：' + str(place.place)

    def end_serves(self):
        self.active = False
        self.save()
        for sm in self.servesmaids_set.filter(active=True):
            sm.deactivate()

        sp = self.servesplaces_set.get(active=True)
        sp.deactivate()

    class Meta:
        verbose_name = "服务"
        verbose_name_plural = verbose_name
        permissions = [
            ("check_in_serves", "Can start a serves"),
            ("change_serves_status", "Can change the status of a serves"),
            ('check_out_serves', "Can check out serves")
        ]


class ServesItems(models.Model):
    serves = models.ForeignKey(Serves, on_delete=models.CASCADE)
    item = models.ForeignKey(Menu, on_delete=models.PROTECT)
    price = models.PositiveSmallIntegerField('单价')
    quantity = models.PositiveSmallIntegerField('数量')

    def __str__(self):
        return str(self.serves) + ' ' + str(self.item)

    class Meta:
        ordering = ['serves']
        verbose_name = "服务项目记录"
        verbose_name_plural = verbose_name


class ServesMaids(models.Model):
    serves = models.ForeignKey(Serves, on_delete=models.CASCADE)
    maid = models.ForeignKey(Maid, on_delete=models.PROTECT)
    price = models.PositiveSmallIntegerField('单价', default=MAID_PRICE)
    start = models.DateTimeField('开始时间', default=now)
    end = models.DateTimeField('结束时间', default=now)
    active = models.BooleanField('进行中', default=True)

    def activate(self):
        self.active = True
        self.save()
        self.maid.available = False
        self.maid.save()

    def deactivate(self):
        self.active = False
        self.save()
        self.maid.available = True
        self.maid.save()

    def update(self):
        self.end = now()
        self.save()

    def save(self, *args, **kwargs):
        self.price = self.maid.price
        super(ServesMaids, self).save(*args, **kwargs)

    def __str__(self):
        return '开始时间：' + show_time(self.start) + ' ' + str(self.maid)

    class Meta:
        ordering = ['maid']
        verbose_name = "服务女仆记录"
        verbose_name_plural = verbose_name


class ServesPlaces(models.Model):
    serves = models.ForeignKey(Serves, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.PROTECT)
    start = models.DateTimeField('开始时间', default=now)
    end = models.DateTimeField('结束时间', default=now)
    price = models.PositiveSmallIntegerField('单价')
    active = models.BooleanField('进行中', default=True)

    def activate(self):
        self.active = True
        self.save()
        self.place.available = False
        self.place.save()

    def deactivate(self):
        self.active = False
        self.save()
        self.place.available = True
        self.place.save()

    def update(self):
        self.end = now()
        self.save()

    def save(self, *args, **kwargs):
        self.price = self.place.price
        super(ServesPlaces, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.place) + ' ' + show_time(self.start) + ' 到 ' + show_time(self.end)

    class Meta:
        ordering = ['place']
        verbose_name = "服务场所记录"
        verbose_name_plural = verbose_name


class VoucherType(models.Model):
    name = models.CharField('名称', max_length=100, unique=True)
    note = models.CharField('使用条件', max_length=200)
    revenue = models.DecimalField('实际收入', decimal_places=2, max_digits=8)
    meituan = models.BooleanField('美团/大众', default=False)
    amount = models.PositiveSmallIntegerField('抵扣金额')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "代金劵种类"
        verbose_name_plural = verbose_name


class Voucher(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, blank=True, null=True)
    type = models.ForeignKey(VoucherType, on_delete=models.PROTECT)
    used = models.BooleanField('已使用', default=False)
    swift_number = models.CharField('流水号', max_length=100, blank=True, null=True, unique=True)

    def __str__(self):
        return str(self.type)

    class Meta:
        verbose_name = "代金券"
        verbose_name_plural = verbose_name


class Bill(models.Model):
    total = models.DecimalField('收款金额', max_digits=8, decimal_places=2, default=0)
    voucher = models.OneToOneField(Voucher, on_delete=models.PROTECT, blank=True, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, blank=True, null=True)

    def __str__(self):
        return '入账：' + self.total

    class Meta:
        verbose_name = "账单"
        verbose_name_plural = verbose_name
        permissions = [
            ("receive_money", "收钱"),
        ]

    def valid_income(self):
        if hasattr(self, 'depositcharge'):
            return 0
        t = 0
        for i in self.income_set.all():
            t += i.amount
        return t

    def save(self, *args, **kwargs):
        t = 0
        for i in self.income_set.all():
            t += i.amount
        if hasattr(self, 'depositpayment'):
            t += self.depositpayment.amount
        if self.voucher:
            t += self.voucher.type.amount
        self.total = t
        super(Bill, self).save(*args, **kwargs)


class DepositPayment(models.Model):
    amount = models.DecimalField('会员卡扣款', decimal_places=2, max_digits=8, default=0)
    card = models.ForeignKey(Card, on_delete=models.PROTECT)
    bill = models.OneToOneField(Bill, on_delete=models.PROTECT)

    def __str__(self):
        return '会员卡扣款： ' + str(self.amount)

    class Meta:
        verbose_name = '会员卡支付'
        verbose_name_plural = verbose_name


class Income(models.Model):
    PAYMENT_METHOD = (('WC', '微信扫码'), ('AP', '支付宝扫码'), ('MP', '小程序付款'),
                      ('CS', '现金支付'), ('RE', '客服号转账'))
    method = models.CharField('支付方式', choices=PAYMENT_METHOD, max_length=2)
    amount = models.DecimalField('金额', max_digits=8, decimal_places=2)
    swift_number = models.CharField('流水号', max_length=100, blank=True, null=True,
                                    validators=[RegexValidator(regex='^[0-9]+$',
                                                               message='请输入正确流水号', code='nomatch')])
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT)

    def save(self, *args, **kwargs):
        super(Income, self).save(*args, **kwargs)
        self.bill.save()

    def __str__(self):
        return str(self.method) + ' ' + str(self.amount)

    class Meta:
        verbose_name = "入账"
        verbose_name_plural = verbose_name
        unique_together = ('method', 'swift_number')


class Charge(models.Model):
    total = models.DecimalField('收款', max_digits=8, decimal_places=2)
    note = models.CharField('备注', max_length=200, blank=True)
    bill = models.OneToOneField(Bill, on_delete=models.PROTECT)
    paid = models.BooleanField('已支付', default=False)

    def __str__(self):
        return '账单： ' + self.total

    class Meta:
        abstract = True
        verbose_name = "收款"
        verbose_name_plural = verbose_name

    def unpaid_amount(self):
        return self.total - self.bill.total


class ServesCharge(Charge):
    serves = models.OneToOneField(Serves, on_delete=models.PROTECT)
    manual = models.IntegerField('核增、核减', default=0)

    def unpaid_amount(self):
        return super().unpaid_amount() + self.manual

    class Meta:
        verbose_name = "服务收款"
        verbose_name_plural = verbose_name


class DepositCharge(Charge):
    deposit_amount = models.DecimalField('储值金额', max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = "充值收款"
        verbose_name_plural = verbose_name


# helper methods
def show_time(time):
    return time.strftime('%Y-%m-%d %H:%M')

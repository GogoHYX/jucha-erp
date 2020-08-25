from django.db import models
from django.utils.timezone import now
from django.core.validators import RegexValidator

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
    active = models.BooleanField('在职')
    fulltime = models.BooleanField('全职')

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


class Customer(models.Model):
    wechat_id = models.CharField('微信号', max_length=40, blank=True, null=True)
    name = models.CharField('姓名', max_length=20, blank=True, null=True)
    phone = models.CharField('手机号', max_length=11,
                             validators=[RegexValidator(regex='^[0-9]{11}$',
                                                        message='请输入正确的11位手机号', code='nomatch')],
                             unique=True, )
    GENDER_CHOICE = ((u'M', u'男'), (u'F', u'女'),)
    gender = models.CharField(max_length=2, choices=GENDER_CHOICE, null=True)
    credit = models.IntegerField('积分', default=0)

    def __str__(self):
        return self.phone

    class Meta:
        verbose_name = "顾客"
        verbose_name_plural = verbose_name


class Deposit(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.PROTECT)
    number = models.CharField('会员卡号', max_length=20, unique=True)
    discount = models.DecimalField('折扣', max_digits=2, decimal_places=1)
    deposit = models.DecimalField('余额', max_digits=8, decimal_places=2)


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


class Serves(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, blank=True)
    place = models.ManyToManyField(Place, through='ServesPlaces')
    start = models.DateTimeField('开始时间', default=now)
    end = models.DateTimeField('结束时间', default=now)
    item = models.ManyToManyField(Menu, through='ServesItems')
    maid = models.ManyToManyField(Maid, through='ServesMaids')
    active = models.BooleanField('进行中', default=True)

    def __str__(self):
        maids = self.servesmaids_set.all()
        place = self.servesplaces_set.all()[0]
        return '开始时间：' + str(self.start) + '\n女仆： ' + \
               ' '.join([str(m.maid) for m in maids]) + '\n场地：' + str(place.place)

    class Meta:
        verbose_name = "服务"
        verbose_name_plural = verbose_name


class ServesItems(models.Model):
    serves = models.ForeignKey(Serves, on_delete=models.CASCADE)
    item = models.ForeignKey(Menu, on_delete=models.PROTECT)
    price = models.PositiveSmallIntegerField('单价')
    quantity = models.PositiveSmallIntegerField('数量')

    def __str__(self):
        return str(self.serves) + ' ' + str(self.item)

    class Meta:
        ordering = ['serves']
        verbose_name = "服务项目"
        verbose_name_plural = verbose_name


class ServesMaids(models.Model):
    serves = models.ForeignKey(Serves, on_delete=models.CASCADE)
    maid = models.ForeignKey(Maid, on_delete=models.PROTECT)
    price = models.PositiveSmallIntegerField('单价', default=MAID_PRICE)
    start = models.DateTimeField('开始时间', default=now)
    end = models.DateTimeField('结束时间', default=now)
    active = models.BooleanField('进行中', default=True)

    def __str__(self):
        return str(self.serves) + ' ' + str(self.maid)

    class Meta:
        ordering = ['serves']
        verbose_name = "服务女仆"
        verbose_name_plural = verbose_name


class ServesPlaces(models.Model):
    serves = models.ForeignKey(Serves, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.PROTECT)
    start = models.DateTimeField('开始时间', default=now)
    end = models.DateTimeField('结束时间', default=now)
    price = models.PositiveSmallIntegerField('单价')
    active = models.BooleanField('进行中', default=True)

    def __str__(self):
        return str(self.serves) + ' ' + str(self.place)

    class Meta:
        ordering = ['start']
        verbose_name = "服务场所"
        verbose_name_plural = verbose_name


class VoucherType(models.Model):
    name = models.CharField('名称', max_length=100, unique=True)
    note = models.CharField('使用条件', max_length=200)
    revenue = models.DecimalField('实际收入', decimal_places=2, max_length=8)
    amount = models.PositiveSmallIntegerField('抵扣金额')

    class Meta:
        verbose_name = "代金劵种类"
        verbose_name_plural = verbose_name


class Voucher(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, blank=True, null=True)
    type = models.ForeignKey(VoucherType, on_delete=models.PROTECT)
    used = models.BooleanField('已使用', default=False)
    meituan = models.BooleanField('美团/大众', default=False)
    swift_number = models.CharField('流水号', blank=True, null=True)

    class Meta:
        unique_together = ('meituan', 'swift_number')
        verbose_name = "代金券"
        verbose_name_plural = verbose_name


class Bill(models.Model):
    total = models.DecimalField('金额', max_digits=8, decimal_places=2, default=0)
    voucher = models.ForeignKey(Voucher, on_delete=models.PROTECT, blank=True, null=True)
    deposit_payment = models.DecimalField('会员卡扣款', decimal_places=2, max_length=8, default=0)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, blank=True, null=True)

    def valid_amount(self):
        valid = 0
        for i in self.income_set.filter(cash_back=True):
            valid += i.amount
        return valid

    class Meta:
        verbose_name = "账单"
        verbose_name_plural = verbose_name


class Income(models.Model):
    PAYMENT_METHOD = (('WC', '微信扫码'), ('AP', '支付宝扫码'), ('MP', '小程序付款'),
                      ('VC', '会员卡扣款'), ('CS', '现金支付'), ('RE', '预约定金'))
    method = models.CharField('支付方式', choices=PAYMENT_METHOD, max_length=2)
    amount = models.DecimalField('金额', max_digits=8, decimal_places=2)
    swift_number = models.CharField('流水号', max_length=100, blank=True, null=True)
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT)
    cash_back = models.BooleanField('可返现', default=True)

    def save(self, *args, **kwargs):
        if self.method == 'VC':
            self.cash_back = False
        super(Income, self).save(*args, **kwargs)
        t = 0
        for i in self.bill.income_set.all():
            t += i.amount
        self.bill.total = t
        self.bill.save()

    class Meta:
        verbose_name = "入账"
        verbose_name_plural = verbose_name
        unique_together = ('method', 'swift_number')


class Charge(models.Model):
    total = models.DecimalField('总额', max_digits=8, decimal_places=2)
    note = models.CharField('备注', max_length=200)
    bill = models.OneToOneField(Bill, on_delete=models.PROTECT)

    def unpaid(self):
        return self.total - self.bill.total

    class Meta:
        abstract = True
        verbose_name = "收款"
        verbose_name_plural = verbose_name


class ServesCharge(Charge):
    serves = models.OneToOneField(Serves, on_delete=models.PROTECT)
    manual = models.IntegerField('核增、核减', default=0)

    def cash_return(self):
        valid_total = self.manual + self.bill.valid_amount()
        return valid_total * CASH_BACK_PERCENTAGE

    class Meta:
        verbose_name = "服务收款"
        verbose_name_plural = verbose_name


class DepositCharge(Charge):
    card = models.OneToOneField(Deposit, on_delete=models.PROTECT)
    deposit_amount = models.DecimalField('储值金额', max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = "充值收款"
        verbose_name_plural = verbose_name

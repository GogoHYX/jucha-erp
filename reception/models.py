from django.db import models
from django.utils.timezone import now
from django.core.validators import RegexValidator


# Create your models here.
class Maid(models.Model):
    id = models.CharField('身份证号',
                          validators=[RegexValidator(regex='^[0-9]{17}[0-9X]$',
                                                     message='请输入正确的身份证号，包含数字和大写X', code='nomatch')],
                          unique=True)
    name = models.CharField('姓名', max_length=5, )
    cos_name = models.CharField('昵称', max_length=5, unique=True)
    birthday = models.DateField('出生年月')
    wechat_id = models.CharField('微信号', unique=True)
    phone = models.CharField('手机号',
                             validators=[RegexValidator(regex='^[0-9]{11}$',
                                                        message='请输入正确的11位手机号', code='nomatch')],
                             unique=True)
    active = models.BooleanField('在职')
    fulltime = models.BooleanField('全职')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "女仆"
        verbose_name_plural = verbose_name


class Customer(models.Model):
    wechat_id = models.CharField('微信号', blank=True)
    phone = models.CharField('手机号',
                             validators=[RegexValidator(regex='^[0-9]{11}$',
                                                        message='请输入正确的11位手机号', code='nomatch')],
                             unique=True, )
    GENDER_CHOICE = ((u'M', u'男'), (u'F', u'女'),)
    gender = models.CharField(max_length=2, choices=GENDER_CHOICE, null=True)
    credit = models.PositiveIntegerField('积分', default=0)

    def __str__(self):
        return self.phone

    class Meta:
        verbose_name = "顾客"
        verbose_name_plural = verbose_name


class Deposit(models.Model):
    customer = models.ForeignKey(Customer, unique=True, on_delete=models.PROTECT)
    number = models.CharField('会员卡号', unique=True)
    deposit = models.DecimalField('余额', decimal_places=2, default=0)


class Place(models.Model):
    name = models.CharField('名称', max_length=10, unique=True)
    price = models.PositiveSmallIntegerField('每小时价格')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "场地"
        verbose_name_plural = verbose_name


class Menu(models.Model):
    item = models.CharField('项目', max_length='20', unique=True)
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
    advanced = models.PositiveSmallIntegerField('定金', default=0)
    through = models.CharField('途径', choices=THROUGH_CHOICE, max_length=2)

    def __str__(self):
        pass

    class Meta:
        verbose_name = "预约"
        verbose_name_plural = verbose_name


class Serves(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    place = models.ForeignKey(Place, on_delete=models.PROTECT)
    start = models.DateTimeField('开始时间', default=now)
    end = models.DateTimeField('结束时间', default=now)
    item = models.ManyToManyField(Menu, through='ServesItems')
    maid = models.ManyToManyField(Maid, through='ServesMaids')
    active = models.BooleanField('进行中', default=True)

    def __str__(self):
        return str(self.start) + '到' + str(self.end)

    class Meta:
        verbose_name = "服务"
        verbose_name_plural = verbose_name


class ServesItems(models.Model):
    serves = models.ForeignKey(Serves, on_delete=models.CASCADE)
    item = models.ForeignKey(Menu, on_delete=models.PROTECT)
    price = models.PositiveSmallIntegerField('单价', default=Menu.objects.get(pk=item).price)
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
    start = models.DateTimeField('开始时间', default=serves.start)
    end = models.DateTimeField('结束时间', default=serves.end)

    def __str__(self):
        return str(self.serves) + ' ' + str(self.maid)

    class Meta:
        ordering = ['serves']
        verbose_name = "服务女仆"
        verbose_name_plural = verbose_name


class Bill(models.Model):
    total = models.DecimalField('金额', decimal_places=2)

    class Meta:
        verbose_name = "账单"
        verbose_name_plural = verbose_name


class Income(models.Model):
    PAYMENT_METHOD = (('WC', '微信扫码'), ('AP', '支付宝扫码'), ('MP', '小程序付款'),
                      ('VC', '会员卡扣款'), ('CS', '现金支付'), ('MT', '美团/大众'),)
    method = models.CharField('支付方式', choices=PAYMENT_METHOD, max_length=2)
    amount = models.DecimalField('金额', decimal_places=2)
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "入账"
        verbose_name_plural = verbose_name


class VoucherType(models.Model):
    name = models.CharField('名称', max_length=100, unique=True)
    note = models.CharField('使用条件', max_length=200)
    amount = models.PositiveSmallIntegerField('金额')

    class Meta:
        verbose_name = "代金劵种类"
        verbose_name_plural = verbose_name


class Voucher(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    type = models.ForeignKey(VoucherType, on_delete=models.PROTECT)
    unused = models.BooleanField('未使用', default=True)
    start = models.DateTimeField('开始日期', default=now)
    end = models.DateTimeField('截止日期')

    class Meta:
        verbose_name = "代金券"
        verbose_name_plural = verbose_name


class Charge(models.Model):
    total = models.DecimalField('总额', decimal_places=2)
    note = models.CharField('备注')
    bill = models.ForeignKey(Bill, unique=True, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "收款"
        verbose_name_plural = verbose_name


class ServesCharge(Charge):
    serves = models.ForeignKey(Serves, unique=True, on_delete=models.PROTECT)
    discount = models.DecimalField('折扣', default=10, max_length=2, decimal_places=1)
    voucher = models.ForeignKey(Voucher, on_delete=models.PROTECT, blank=True, null=True)
    manual = models.PositiveIntegerField('核增、核减', default=0)

    class Meta:
        verbose_name = "服务收款"
        verbose_name_plural = verbose_name


class DepositCharge(Charge):
    card = models.ForeignKey(Deposit, unique=True, on_delete=models.PROTECT)
    deposit_amount = models.DecimalField('储值金额', decimal_places=2)

    class Meta:
        verbose_name = "充值收款"
        verbose_name_plural = verbose_name




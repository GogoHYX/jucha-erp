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

    def __str__(self):
        return self.phone

    class Meta:
        ordering = ['name']
        verbose_name = "顾客"
        verbose_name_plural = verbose_name


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
    item = models.CharField('项目', max_length='20')
    price = models.PositiveSmallIntegerField('单价')
    active = models.BooleanField('仍在提供')

    def __str__(self):
        return self.item

    class Meta:
        ordering = ['item']
        verbose_name = "价目表"
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
        ordering = ['name']
        verbose_name = "场地"
        verbose_name_plural = verbose_name


class ServesItems(models.Model):
    serves = models.ForeignKey(Serves, on_delete=models.CASCADE)
    item = models.ForeignKey(Menu, on_delete=models.PROTECT)
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
    serves = models.ForeignKey(Serves)
    PAYMENT_METHOD = (('WX', '微信扫码'), ('AP', '支付宝扫码'), ('MP', '小程序付款'), ('VC', '会员卡扣款'))


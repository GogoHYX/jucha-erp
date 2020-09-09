from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Maid)
admin.site.register(Place)
admin.site.register(Customer)
admin.site.register(Serves)
admin.site.register(ServesMaids)
admin.site.register(ServesPlaces)
admin.site.register(Menu)
admin.site.register(ServesItems)
admin.site.register(Bill)
admin.site.register(ServesCharge)
admin.site.register(Voucher)
admin.site.register(VoucherType)
admin.site.register(Card)
admin.site.register(Income)
admin.site.register(DepositPayment)

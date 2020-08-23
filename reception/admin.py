from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Maid)
admin.site.register(Place)
admin.site.register(Customer)
admin.site.register(Serves)
admin.site.register(ServesMaids)
admin.site.register(ServesPlaces)
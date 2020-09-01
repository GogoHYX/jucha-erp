from django.urls import path

from . import views

app_name = 'reception'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('check-in/', views.check_in, name='check_in'),
    path('ongoing-serves/', views.ongoing_serves, name='ongoing_serves'),
    path('serves/<int:serves_id>/', views.serves_detail, name='serves_detail'),
    path('serves/<int:serves_id>/change/', views.serves_change, name='change_status'),
    path('serves/<int:serves_id>/add-item/', views.add_item, name='add_item'),
    path('serves/<int:serves_id>/check-out/', views.check_out, name='check_out'),
    path('pay/<int:bill_id>/', views.pay, name='pay'),
    path('add-payment/<int:bill_id>/', views.add_payment, name='add_payment'),
    path('deposit-payment/<int:bill_id>/', views.use_deposit, name='use_deposit'),
    path('use-voucher/<int:bill_id>/', views.use_voucher, name='use_voucher'),
    path('use-meituan/<int:bill_id>/', views.use_meituan, name='use_meituan'),
    path('done/<int:bill_id>/', views.done, name='done'),
]
from django.urls import path

from . import views

app_name = 'reception'

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('set-schedule/', views.set_schedule, name='set_schedule'),
    path('check-in/', views.check_in, name='check_in'),
    path('ongoing/', views.ongoing, name='ongoing'),
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
    path('create-card/<int:customer_id>/', views.create_card, name='create_card'),
    path('customer/', views.customer_detail, name='customer_detail'),
    path('credit-redeem/<int:customer_id>/', views.credit_redeem, name='credit_redeem'),
    path('manage/set-schedule', views.set_schedule, name='set_schedule'),
]
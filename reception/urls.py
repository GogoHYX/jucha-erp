from django.urls import path

from . import views

app_name = 'reception'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('check-in/', views.check_in, name='check_in'),
    path('serves/<int:serves_id>/', views.serves_detail, name='serves_detail'),
    path('serves/<int:serves_id>/change/', views.serves_change, name='change_status'),
    path('serves/<int:serves_id>/add-item/', views.add_item, name='add_item'),
    path('serves/<int:serves_id>/check-out/', views.check_out, name='check_out'),
    path('serves/<int:bill_id>/pay/', views.pay, name='pay'),
    path('serves/<int:bill_id>/add-payment/', views.add_payment, name='add_payment'),
]
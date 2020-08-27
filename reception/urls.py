from django.urls import path

from . import views

app_name = 'reception'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('check-in/', views.check_in, name='check_in'),
    path('serves/<int:serves_id>/', views.serves_detail, name='serves_detail'),
    path('serves/<int:serves_id>/change/', views.serves_change, name='change_status')
]
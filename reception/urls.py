from django.urls import path

from . import views

app_name = 'reception'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('check-in/', views.check_in, name='check_in'),
    path('check-out/', views.check_out, name='check_out'),
]
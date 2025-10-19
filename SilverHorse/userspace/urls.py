from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),   # головна сторінка профілю
    path('dashboard/', views.dashboard_view, name='dashboard'),  # якщо хочеш окремий URL
    path('logout/', views.logout_view, name='logout'),  # вихід
]

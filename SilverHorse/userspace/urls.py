from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),             # головна сторінка профілю
    path('dashboard/messages/', views.messages_page, name='messages_page'),  # сторінка повідомлень
    path('dashboard/send/', views.send_message, name='send_message'),        # написати повідомлення
    path('logout/', views.logout_view, name='logout'),                       # вихід
    path('sources/', views.sources, name='sources'),                         # сторінка джерел
]

# userspace/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),              # головна сторінка профілю
    path('dashboard/messages/', views.messages_page, name='messages_page'),  # сторінка повідомлень
    path('logout/', views.logout_view, name='logout'),                       # вихід
    path('sources/', views.sources, name='sources'),                         # сторінка джерел
    path('block/', views.block_user_view, name='block_user'),                # блокування користувачів
    path('unblock/<int:user_id>/', views.unblock_user_view, name='unblock_user'),  # розблокування користувачів
]

from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),             # головна сторінка профілю
    path('dashboard/messages/', views.messages_page, name='messages_page'),  # сторінка повідомлень
    # Якщо у тебе немає окремої send_message функції, цей рядок прибери або закоментуй
    #path('dashboard/send/', views.send_message, name='send_message'),
    path('logout/', views.logout_view, name='logout'),                       # вихід
    path('sources/', views.sources, name='sources'),                         # сторінка джерел
]

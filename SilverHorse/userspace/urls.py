# userspace/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/messages/', views.messages_page, name='messages_page'),
    path('logout/', views.logout_view, name='logout'),
    path('sources/', views.sources, name='sources'),
    path('block/', views.block_user_view, name='block_user'),
    path('unblock/<int:user_id>/', views.unblock_user_view, name='unblock_user'),

    # ⚡ Позначити системне повідомлення як прочитане
    path(
        'system_message/<int:message_id>/read/',
        views.mark_message_read,
        name='mark_message_read'
    ),

    path('profile/', views.profile_page, name='profile_page'),
    path('subscription/', views.subscription_page, name='subscription_page'),
    path('account/', views.account_page, name='account_page'),
    path('language/', views.language_page, name='language_page'),

    path('horses/', views.horses_page, name='horses_page'),
    path('equestrian/', views.equestrian_page, name='equestrian_page'),  # тут все відображається
    path('trade/', views.market_view, name='trade_page'),

    path('horse/<int:horse_id>/', views.horse_detail, name='horse_detail'),
    path('buy/<int:horse_id>/', views.buy_horse, name='buy_horse'),

    path('skip-tutorial/', views.skip_tutorial, name='skip_tutorial'),
    path('start-tutorial/', views.start_tutorial, name='start_tutorial'),

    path('horses/update_stat/<int:horse_id>/', views.update_horse_stat, name='update_horse_stat'),

    path('shelter/', views.shelter_view, name='shelter_page'),
    path('shelter/send/<int:horse_id>/', views.send_to_shelter, name='send_to_shelter'),
]

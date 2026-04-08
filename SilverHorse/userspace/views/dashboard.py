from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import date, datetime
import random
from ..models import (
    Horse, Message, EquestrianComplex, ComplexResource,
    Auction, BreedingOffer, Profile
)


@login_required
def dashboard_view(request):
    user = request.user
    profile = user.profile

    # Час доби для привітання
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Доброго ранку"
    elif hour < 18:
        greeting = "Доброго дня"
    else:
        greeting = "Доброго вечора"

    # Комплекс
    complex_obj = EquestrianComplex.objects.filter(owner=user).first()
    has_complex = complex_obj is not None
    if has_complex:
        complex_name = complex_obj.name
        complex_prestige = complex_obj.prestige
        total_resources = ComplexResource.objects.filter(complex=complex_obj).aggregate(
            total=Sum('quantity')
        )['total'] or 0
    else:
        complex_name = None
        complex_prestige = 0
        total_resources = 0

    # Коні користувача
    user_horses = Horse.objects.filter(owner=user, status='user')
    horses_count = user_horses.count()
    total_wins = user_horses.aggregate(total=Sum('wins'))['total'] or 0
    best_horse = user_horses.order_by('-wins').first()

    # 🎲 ВИПАДКОВИЙ КІНЬ (оновлюється при кожному запиті)
    if horses_count > 0:
        random_horse = random.choice(list(user_horses))
    else:
        random_horse = Horse.objects.filter(status='market').order_by('?').first()

    if random_horse:
        random_horse_total_skills = (
                random_horse.speed + random_horse.endurance +
                random_horse.strength + random_horse.dressage +
                random_horse.gallop + random_horse.trot + random_horse.jumping
        )
    else:
        random_horse_total_skills = 0

    # Кінь дня (залишаємо для іншого блоку)
    horse_of_the_day = None
    if horses_count > 0:
        index = date.today().toordinal() % horses_count
        horse_of_the_day = user_horses[index]

    # Валюти
    horseshoes = profile.horseshoes
    silver_wings = profile.silver_wings
    reserved_horseshoes = profile.reserved_horseshoes
    reserved_silver_wings = profile.reserved_silver_wings

    # Активність на ринках
    active_auctions_count = Auction.objects.filter(seller=user, is_active=True).count()
    active_breeding_count = BreedingOffer.objects.filter(owner=user, is_active=True).count()

    # Непрочитані повідомлення
    unread_messages_count = Message.objects.filter(receiver=user, is_read=False).count()

    # Рекомендований кінь на продаж (випадковий)
    recommended_horse = Horse.objects.filter(status='market').order_by('?').first()

    # Пропозиції / реклама
    promo_offers = [
        {"title": "Отримай 100 Срібних Підков!", "link": "#", "icon": "gift"},
        {"title": "Новий кінь у магазині!", "link": "#", "icon": "horse"},
        {"title": "Знижка 20% на тренування!", "link": "#", "icon": "tag"},
    ]

    context = {
        'greeting': greeting,
        'has_complex': has_complex,
        'complex': complex_obj,
        'complex_name': complex_name,
        'complex_prestige': complex_prestige,
        'total_resources': total_resources,
        'horses_count': horses_count,
        'total_wins': total_wins,
        'best_horse': best_horse,
        'horse_of_the_day': horse_of_the_day,
        'random_horse': random_horse,
        'random_horse_total_skills': random_horse_total_skills,
        'horseshoes': horseshoes,
        'silver_wings': silver_wings,
        'reserved_horseshoes': reserved_horseshoes,
        'reserved_silver_wings': reserved_silver_wings,
        'active_auctions_count': active_auctions_count,
        'active_breeding_count': active_breeding_count,
        'unread_messages_count': unread_messages_count,
        'recommended_horse': recommended_horse,
        'promo_offers': promo_offers,
        'is_new_user': profile.is_new_user,
        'new_messages_count': unread_messages_count,
        'total_competitions': 0,
        'total_earnings': 0,
        'overall_rank': 0,
    }
    return render(request, 'userspace/dashboard/dashboard.html', context)


@login_required
def skip_tutorial(request):
    request.user.profile.is_new_user = False
    request.user.profile.save()
    return redirect('dashboard')


@login_required
def start_tutorial(request):
    request.user.profile.is_new_user = False
    request.user.profile.save()
    return redirect('dashboard')
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import date
from ..models import Horse, Message

@login_required
def dashboard_view(request):
    user = request.user
    profile = user.profile

    # Комплекс
    complex_obj = EquestrianComplex.objects.filter(owner=user).first()
    has_complex = complex_obj is not None

    # Коні користувача
    user_horses = Horse.objects.filter(owner=user, status='user')
    horses_count = user_horses.count()

    # Кінь дня
    horse_of_the_day = None
    if horses_count > 0:
        index = date.today().toordinal() % horses_count
        horse_of_the_day = user_horses[index]

    # Статистика
    wins_count = user_horses.aggregate(total=Sum('wins'))['total'] or 0
    total_competitions = 0  # поки немає змагань
    total_earnings = 0  # поки немає заробітку
    overall_rank = 0  # поки не рахували рейтинг

    # Нові повідомлення
    new_messages_count = Message.objects.filter(receiver=user, is_read=False).count()

    # Рекомендований кінь на продаж (покажемо випадковий)
    recommended_horse = Horse.objects.filter(status='market').order_by('?').first()

    # Пропозиції / реклама
    promo_offers = [
        {"title": "Отримай 100 Срібних Підков!", "link": "#"},
        {"title": "Новий кінь у магазині!", "link": "#"},
        {"title": "Знижка 20% на тренування!", "link": "#"},
    ]

    # Кількість непрочитаних повідомлень користувача
    unread_messages_count = Message.objects.filter(receiver=user, is_read=False).count()

    context = {
        'has_complex': has_complex,
        'complex': complex_obj,
        'horses_count': horses_count,
        'horse_of_the_day': horse_of_the_day,
        'wins_count': wins_count,
        'total_competitions': total_competitions,
        'total_earnings': total_earnings,
        'overall_rank': overall_rank,
        'is_new_user': profile.is_new_user,
        'new_messages_count': new_messages_count,
        'recommended_horse': recommended_horse,
        'promo_offers': promo_offers,
        'unread_messages_count': unread_messages_count,
    }

    return render(request, 'userspace/dashboard.html', context)


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
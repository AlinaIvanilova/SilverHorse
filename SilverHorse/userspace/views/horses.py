from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from ..models import Horse
from django.utils import timezone
from ..models import Auction

@login_required
def horses_page(request):
    # Куплені коні користувача
    user_horses = Horse.objects.filter(owner=request.user, status='user')
    return render(request, 'userspace/horses.html', {'user_horses': user_horses})



@login_required
def horse_detail(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id)

    prev_horse = None
    next_horse = None

    # Навігація тільки для своїх коней
    if horse.owner == request.user and horse.status == 'user':
        user_horses = list(
            Horse.objects.filter(owner=request.user, status='user').order_by('id')
        )

        if horse in user_horses:
            current_index = user_horses.index(horse)

            prev_horse = user_horses[current_index - 1] if current_index > 0 else None
            next_horse = (
                user_horses[current_index + 1]
                if current_index < len(user_horses) - 1
                else None
            )

    return render(request, 'userspace/horse_detail.html', {
        'horse': horse,
        'prev_horse': prev_horse,
        'next_horse': next_horse,
    })
# -------------------------
# Покупка коня
# -------------------------
@login_required
def buy_horse(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id)
    buyer_profile = request.user.profile

    # Перевіряємо, чи кінь на ринку
    if horse.status != 'market':
        messages.error(request, "Цей кінь вже не продається.")
        return redirect('market_page')

    # Перевіряємо, чи користувачу вистачає підков
    if buyer_profile.horseshoes < horse.price:
        messages.error(request, "У вас недостатньо Срібних Підков для покупки.")
        return redirect('market_page')

    # Знімаємо гроші
    buyer_profile.horseshoes -= horse.price
    buyer_profile.save()

    # Передаємо власність користувачу
    horse.owner = request.user
    horse.status = 'user'
    horse.save()

    messages.success(request, f"Вітаємо! Ви купили коня {horse.name} 🐎")
    return redirect('horses_page')


@login_required
@csrf_exempt
def update_horse_stat(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id, owner=request.user)
    if request.method == 'POST':
        data = json.loads(request.body)
        stat = data.get('stat')
        delta = data.get('delta', 0)
        try:
            delta = int(delta)
        except:
            delta = 0

        horse.adjust_stat(stat, delta)
        return JsonResponse({'success': True, 'new_value': getattr(horse, stat)})
    return JsonResponse({'success': False})


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Horse
import random


@login_required
def breed_select(request, horse_id):
    """Show list of potential mates for the given horse."""
    horse = get_object_or_404(Horse, id=horse_id, owner=request.user, status='user')

    # Перевірка віку (мінімум 3 роки)
    if horse.age < 3:
        messages.error(request, f"{horse.name} занадто молодий для розмноження. Мінімальний вік – 3 роки.")
        return redirect('horse_detail', horse_id=horse.id)

    # Знаходимо коней протилежної статі, що належать користувачу, статус 'user', вік >= 3
    opposite_gender = 'F' if horse.gender == 'M' else 'M'
    potential_mates = Horse.objects.filter(
        owner=request.user,
        status='user',
        gender=opposite_gender,
        age__gte=3  # також перевіряємо вік партнера
    ).exclude(id=horse.id)

    return render(request, 'userspace/breed_select.html', {
        'horse': horse,
        'potential_mates': potential_mates
    })


@login_required
def breed_confirm(request, horse1_id, horse2_id):
    """Create a new foal from two horses."""
    # Отримуємо обох коней, перевіряємо, що вони належать користувачу і придатні для розмноження
    horse1 = get_object_or_404(Horse, id=horse1_id, owner=request.user, status='user')
    horse2 = get_object_or_404(Horse, id=horse2_id, owner=request.user, status='user')

    # Перевірка статі
    if horse1.gender == horse2.gender:
        messages.error(request, "Коні повинні бути різної статі для розмноження.")
        return redirect('breed_select', horse_id=horse1.id)

    # Перевірка віку
    if horse1.age < 3 or horse2.age < 3:
        messages.error(request, "Обидва коні повинні бути віком від 3 років для розмноження.")
        return redirect('breed_select', horse_id=horse1.id)

    # Визначаємо матір і батька
    mother = horse1 if horse1.gender == 'F' else horse2
    father = horse2 if mother == horse1 else horse1

    # Генеруємо риси лошати
    # Порода: випадкова від батьків (або однакова, якщо однакові)
    if mother.breed == father.breed:
        breed = mother.breed
    else:
        breed = random.choice([mother.breed, father.breed])

    # Колір: випадковий від батьків
    coat_color = random.choice([mother.coat_color, father.coat_color])

    # Стать: випадкова
    gender = random.choice(['M', 'F'])

    # Характеристики: середнє + випадкове відхилення
    def inherit_stat(stat_name):
        avg = (getattr(mother, stat_name) + getattr(father, stat_name)) // 2
        variation = random.randint(-5, 5)
        return max(1, min(100, avg + variation))

    speed = inherit_stat('speed')
    endurance = inherit_stat('endurance')
    strength = inherit_stat('strength')
    health = 100
    energy = 100
    mood = 100

    # Ім'я (можна змінити пізніше)
    name = f"Лоша {mother.name}"

    # Створюємо нового коня
    foal = Horse.objects.create(
        name=name,
        breed=breed,
        age=1,
        gender=gender,
        coat_color=coat_color,
        speed=speed,
        endurance=endurance,
        strength=strength,
        health=health,
        energy=energy,
        mood=mood,
        owner=request.user,
        price=0,
        status='user',
        wins=0,
        for_sale=False,
    )

    messages.success(request, f"Вітаємо! У вас народилося лоша на ім'я {foal.name}!")
    return redirect('horse_detail', horse_id=foal.id)


@login_required
def sell_horse(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id, owner=request.user, status='user')

    if request.method == 'POST':
        sale_type = request.POST.get('sale_type')  # 'market' або 'auction'
        price = int(request.POST.get('price', 0))
        currency = request.POST.get('currency', 'horseshoes')

        if sale_type == 'market':
            # Виставлення на ринок
            horse.price = price
            horse.status = 'market'
            horse.save()
            messages.success(request, f"{horse.name} виставлений на ринок за {price} підков.")
            return redirect('trade_page')

        elif sale_type == 'auction':
            # Створення аукціону
            # Видаляємо попередні аукціони для цього коня (якщо були)
            Auction.objects.filter(horse=horse).delete()

            end_time = timezone.now() + timezone.timedelta(hours=50)
            auction = Auction.objects.create(
                horse=horse,
                seller=request.user,
                end_time=end_time,
                starting_price=price,
                current_bid=price,
                current_bidder=None,
                currency=currency,
                is_active=True
            )
            horse.status = 'auction'
            horse.save()

            messages.success(request, f"Аукціон для {horse.name} створено!")
            return redirect('auction_detail', auction_id=auction.id)

        else:
            messages.error(request, "Невірний тип продажу.")
            return redirect('sell_horse', horse_id=horse.id)

    # GET: показати форму
    return render(request, 'userspace/sell_horse.html', {'horse': horse})

@login_required
def cancel_sale(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id, owner=request.user, status='market')
    if request.method == 'POST':
        horse.status = 'user'
        horse.price = 0  # можна скинути ціну або залишити
        horse.save()
        messages.success(request, f"Продаж {horse.name} скасовано. Кінь повернуто до вашої стайні.")
        return redirect('horse_detail', horse_id=horse.id)
    # Якщо GET, можна показати сторінку підтвердження або просто перенаправити з повідомленням
    return redirect('horse_detail', horse_id=horse.id)
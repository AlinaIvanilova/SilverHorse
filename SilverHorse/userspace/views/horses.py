from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from ..models import Horse
from django.utils import timezone
from ..models import Auction
import random

@login_required
def horses_page(request):
    user_horses = Horse.objects.filter(owner=request.user, status='user')
    return render(request, 'userspace/horses.html', {'user_horses': user_horses})

@login_required
def horse_detail(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id)

    prev_horse = None
    next_horse = None

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

@login_required
def buy_horse(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id)
    buyer_profile = request.user.profile

    if horse.status != 'market':
        messages.error(request, "Цей кінь вже не продається.")
        return redirect('market_page')

    if buyer_profile.horseshoes < horse.price:
        messages.error(request, "У вас недостатньо Срібних Підков для покупки.")
        return redirect('market_page')

    buyer_profile.horseshoes -= horse.price
    buyer_profile.save()

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


@login_required
def breed_select(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id, owner=request.user, status='user')

    # Перевірка віку – мінімум 36 місяців (3 роки)
    if horse.age < 36:
        messages.error(request, f"{horse.name} занадто молодий для розмноження. Мінімальний вік – 3 роки.")
        return redirect('horse_detail', horse_id=horse.id)

    opposite_gender = 'F' if horse.gender == 'M' else 'M'
    potential_mates = Horse.objects.filter(
        owner=request.user,
        status='user',
        gender=opposite_gender,
        age__gte=36
    ).exclude(id=horse.id)

    return render(request, 'userspace/breed_select.html', {
        'horse': horse,
        'potential_mates': potential_mates
    })

@login_required
def breed_confirm(request, horse1_id, horse2_id):
    horse1 = get_object_or_404(Horse, id=horse1_id, owner=request.user, status='user')
    horse2 = get_object_or_404(Horse, id=horse2_id, owner=request.user, status='user')

    if horse1.gender == horse2.gender:
        messages.error(request, "Коні повинні бути різної статі для розмноження.")
        return redirect('breed_select', horse_id=horse1.id)

    if horse1.age < 36 or horse2.age < 36:
        messages.error(request, "Обидва коні повинні бути віком від 3 років для розмноження.")
        return redirect('breed_select', horse_id=horse1.id)

    mother = horse1 if horse1.gender == 'F' else horse2
    father = horse2 if mother == horse1 else horse1

    if mother.breed == father.breed:
        breed = mother.breed
    else:
        breed = random.choice([mother.breed, father.breed])

    coat_color = random.choice([mother.coat_color, father.coat_color])
    gender = random.choice(['M', 'F'])

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

    name = f"Лоша {mother.name}"

    foal = Horse.objects.create(
        name=name,
        breed=breed,
        age=0,  # новонароджене – 0 місяців
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
        sale_type = request.POST.get('sale_type')
        price = int(request.POST.get('price', 0))
        currency = request.POST.get('currency', 'horseshoes')

        if sale_type == 'market':
            horse.price = price
            horse.status = 'market'
            horse.save()
            messages.success(request, f"{horse.name} виставлений на ринок за {price} підков.")
            return redirect('trade_page')

        elif sale_type == 'auction':
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

    return render(request, 'userspace/sell_horse.html', {'horse': horse})

@login_required
def cancel_sale(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id, owner=request.user, status='market')
    if request.method == 'POST':
        horse.status = 'user'
        horse.price = 0
        horse.save()
        messages.success(request, f"Продаж {horse.name} скасовано. Кінь повернуто до вашої стайні.")
        return redirect('horse_detail', horse_id=horse.id)
    return redirect('horse_detail', horse_id=horse.id)

@login_required
def sleep_horse(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id, owner=request.user, status='user')
    # Додаємо 2 місяці до віку та повністю відновлюємо енергію
    horse.age += 2
    horse.energy = 100
    horse.save()
    messages.success(request, f"{horse.name} добре відпочив і відновив енергію! Вік збільшився на 2 місяці.")
    return redirect('horse_detail', horse_id=horse.id)
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
from django.db import transaction

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

    # Обчислюємо суму навичок
    total_skills = (
        horse.endurance + horse.speed + horse.dressage +
        horse.gallop + horse.trot + horse.jumping
    )

    return render(request, 'userspace/horse_detail.html', {
        'horse': horse,
        'prev_horse': prev_horse,
        'next_horse': next_horse,
        'now': timezone.now(),
        'total_skills': total_skills,
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
        age__gte=36,
        is_pregnant = False
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

    # Визначаємо матір і батька
    mother = horse1 if horse1.gender == 'F' else horse2
    father = horse2 if mother == horse1 else horse1

    # Перевіряємо, чи мати не вагітна
    if mother.is_pregnant:
        messages.error(request, f"{mother.name} вже вагітна і не може брати участь у розмноженні.")
        return redirect('breed_select', horse_id=horse1.id)

    # Записуємо батька для матері
    mother.sire = father
    mother.is_pregnant = True
    mother.pregnancy_due_age = mother.age + 12  # пологи через 12 місяців
    mother.save()

    messages.success(request, f"{mother.name} запліднена! Вона народить лоша через 12 місяців.")
    return redirect('horse_detail', horse_id=mother.id)

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

    today = timezone.now().date()
    if horse.last_sleep and horse.last_sleep.date() == today:
        messages.error(request, f"{horse.name} вже відпочивав сьогодні. Спробуйте завтра!")
        return redirect('horse_detail', horse_id=horse.id)

    horse.age += 2
    horse.energy = 100
    horse.last_sleep = timezone.now()
    horse.save()

    # Перевіряємо пологи
    if horse.is_pregnant and horse.pregnancy_due_age and horse.age >= horse.pregnancy_due_age:
        foal = give_birth(request, horse)
        if foal:
            return redirect('horse_detail', horse_id=foal.id)
        else:
            return redirect('horse_detail', horse_id=horse.id)

    messages.success(request, f"{horse.name} добре відпочив і відновив енергію! Вік збільшився на 2 місяці.")
    return redirect('horse_detail', horse_id=horse.id)

def give_birth(request, mother):
    """Створює лоша від матері та її sire. Повертає об'єкт лошати."""
    father = mother.sire
    if not father:
        mother.is_pregnant = False
        mother.pregnancy_due_age = None
        mother.save()
        return None

    # Генерація рис (як у breed_confirm)
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

    name = f"Лоша {mother.name}"  # тимчасове ім'я

    foal = Horse.objects.create(
        name=name,
        breed=breed,
        age=0,
        gender=gender,
        coat_color=coat_color,
        speed=speed,
        endurance=endurance,
        strength=strength,
        health=health,
        energy=energy,
        mood=mood,
        owner=mother.owner,
        price=0,
        status='user',
        wins=0,
        for_sale=False,
        original_owner=mother.owner,
        name_customized=False,
        sire=father,
        dam=mother,
    )

    # Скидаємо вагітність матері
    mother.is_pregnant = False
    mother.pregnancy_due_age = None
    mother.sire = None
    mother.save()

    messages.success(request, f"У {mother.name} народилося лоша! Дайте йому ім'я.")
    return foal

@login_required
def change_foal_name(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id)

    if horse.original_owner != request.user:
        messages.error(request, "Тільки первинний власник може змінити ім'я лошати.")
        return redirect('horse_detail', horse_id=horse.id)

    if horse.name_customized:
        messages.error(request, "Ви вже змінювали ім'я цього коня.")
        return redirect('horse_detail', horse_id=horse.id)

    if request.method == 'POST':
        new_name = request.POST.get('name', '').strip()
        if new_name:
            horse.name = new_name
            horse.name_customized = True
            horse.save()
            messages.success(request, f"Ім'я змінено на {new_name}.")
        else:
            messages.error(request, "Ім'я не може бути порожнім.")

    return redirect('horse_detail', horse_id=horse.id)

@login_required
def horse_pedigree(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id)

    pedigree = {
        'id': horse.id,
        'name': horse.name,
        'breed': horse.breed,
        'photo_url': horse.get_photo_url(),
        'sire': None,
        'dam': None,
    }

    generations = 3

    def get_ancestors(h, depth, parent_dict):
        if depth > generations or h is None:
            return

        sire = h.sire
        if sire:
            parent_dict['sire'] = {
                'id': sire.id,
                'name': sire.name,
                'breed': sire.breed,
                'photo_url': sire.get_photo_url(),
                'sire': None,
                'dam': None,
            }
            get_ancestors(sire, depth + 1, parent_dict['sire'])
        else:
            parent_dict['sire'] = None

        dam = h.dam
        if dam:
            parent_dict['dam'] = {
                'id': dam.id,
                'name': dam.name,
                'breed': dam.breed,
                'photo_url': dam.get_photo_url(),
                'sire': None,
                'dam': None,
            }
            get_ancestors(dam, depth + 1, parent_dict['dam'])
        else:
            parent_dict['dam'] = None

    get_ancestors(horse, 1, pedigree)

    return render(request, 'userspace/horse_pedigree.html', {
        'horse': horse,
        'pedigree': pedigree,
    })

@login_required
def horse_offspring(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id)
    offspring_as_sire = Horse.objects.filter(sire=horse)
    offspring_as_dam = Horse.objects.filter(dam=horse)
    offspring = (offspring_as_sire | offspring_as_dam).distinct().order_by('-age')
    return render(request, 'userspace/horse_offspring.html', {
        'horse': horse,
        'offspring': offspring,
    })

# ----- НОВА ФУНКЦІЯ ДЛЯ ПРОГУЛЯНКИ -----
@login_required
def walk_horse(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id)

    # Перевіряємо, що кінь належить користувачеві
    if horse.owner != request.user:
        messages.error(request, "Ви не можете гуляти з чужим конем.")
        return redirect('horse_detail', horse_id=horse.id)

    # Перевіряємо статус – тільки власний кінь зі статусом 'user'
    if horse.status != 'user':
        messages.error(request, "Ви можете гуляти лише зі своїм конем, який у вас у стайні.")
        return redirect('horse_detail', horse_id=horse.id)

    # Перевіряємо достатність енергії
    if horse.energy < 10:
        messages.error(request, f"У {horse.name} недостатньо енергії для прогулянки. Потрібно 10, є {horse.energy}.")
        return redirect('horse_detail', horse_id=horse.id)

    # Зменшуємо енергію на 10 і зберігаємо
    horse.energy -= 10
    horse.save()
    messages.success(request, f"Ви погуляли з {horse.name}. Енергія зменшена на 10 (тепер {horse.energy}).")

    return redirect('horse_detail', horse_id=horse.id)

@login_required
def walk_multiple(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id)

    # Перевірки
    if horse.owner != request.user:
        messages.error(request, "Ви не можете гуляти з чужим конем.")
        return redirect('horse_detail', horse_id=horse.id)

    if horse.status != 'user':
        messages.error(request, "Ви можете гуляти лише зі своїм конем, який у вас у стайні.")
        return redirect('horse_detail', horse_id=horse.id)

    if request.method != 'POST':
        return redirect('horse_detail', horse_id=horse.id)

    walks = int(request.POST.get('walks', 0))
    if walks <= 0:
        messages.error(request, "Кількість прогулянок має бути більше 0.")
        return redirect('horse_detail', horse_id=horse.id)

    total_cost = walks * 10
    if horse.energy < total_cost:
        messages.error(request, f"Недостатньо енергії. Потрібно {total_cost}, у коня {horse.energy}.")
        return redirect('horse_detail', horse_id=horse.id)

    with transaction.atomic():
        horse.energy -= total_cost
        horse.save()

    messages.success(request, f"Ви погуляли з {horse.name} {walks} разів. Витрачено {total_cost} енергії.")
    return redirect('horse_detail', horse_id=horse.id)
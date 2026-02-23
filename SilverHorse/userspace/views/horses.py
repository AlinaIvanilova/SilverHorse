from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from ..models import Horse


@login_required
def horses_page(request):
    # Куплені коні користувача
    user_horses = Horse.objects.filter(owner=request.user, status='user')
    return render(request, 'userspace/horses.html', {'user_horses': user_horses})



@login_required
def horse_detail(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id, owner=request.user)

    # Отримуємо ВСІХ коней користувача
    user_horses = list(Horse.objects.filter(owner=request.user, status='user').order_by('id'))

    # Знаходимо індекс поточного коня
    current_index = user_horses.index(horse)

    # Визначаємо попереднього коня
    prev_horse = user_horses[current_index - 1] if current_index > 0 else None

    # Визначаємо наступного коня
    next_horse = user_horses[current_index + 1] if current_index < len(user_horses) - 1 else None

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
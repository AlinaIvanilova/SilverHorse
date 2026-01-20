from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg, Q
from datetime import date
from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Імпорти моделей
from .models import (
    Message, Note, BlockedUser, SystemMessage, Notification, Horse,
    Profile, EquestrianComplex, ComplexRating
)

# Імпорти форм
from .forms import (
    MessageForm, NoteForm, BlockUserForm,
    EquestrianComplexForm, RatingForm
)



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
    total_earnings = 0      # поки немає заробітку
    overall_rank = 0         # поки не рахували рейтинг

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


# -------------------------
# Вихід з акаунта
# -------------------------
def logout_view(request):
    logout(request)
    return redirect('home')


# -------------------------
# Сторінка джерел
# -------------------------
def sources(request):
    return render(request, 'userspace/sources.html')


# -------------------------
# Головна сторінка повідомлень, нотаток і чорного списку
# -------------------------
@login_required
def messages_page(request):
    message_form = MessageForm(request.POST or None, prefix='msg')
    note_form = NoteForm(request.POST or None, prefix='note')
    block_form = BlockUserForm(request.POST or None, prefix='block')

    # Відправлення повідомлення
    if request.method == 'POST' and 'msg-submit' in request.POST:
        if message_form.is_valid():
            receiver_username = message_form.cleaned_data['receiver_username']
            text = message_form.cleaned_data['text']
            try:
                receiver = User.objects.get(username=receiver_username)
                # Перевірка чорного списку
                if BlockedUser.objects.filter(blocker=request.user, blocked=receiver).exists():
                    messages.error(request, f"Ви заблокували {receiver_username} — повідомлення неможливо відправити.")
                    return redirect('messages_page')
                if BlockedUser.objects.filter(blocker=receiver, blocked=request.user).exists():
                    messages.error(request, f"Ви не можете писати {receiver_username}, бо ви у нього в чорному списку.")
                    return redirect('messages_page')

                Message.objects.create(sender=request.user, receiver=receiver, text=text)
                messages.success(request, f"Повідомлення відправлено користувачу {receiver_username}.")
            except User.DoesNotExist:
                messages.error(request, "Користувача з таким ім'ям не існує.")
            return redirect('messages_page')

    # Створення нотатки
    if request.method == 'POST' and 'note-submit' in request.POST:
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.user = request.user
            note.save()
            messages.success(request, "Нотатка збережена.")
            return redirect('messages_page')

    # Блокування користувача
    if request.method == 'POST' and 'block-submit' in request.POST:
        if block_form.is_valid():
            username = block_form.cleaned_data['username']
            try:
                user_to_block = User.objects.get(username=username)
                if user_to_block == request.user:
                    messages.error(request, "Ви не можете заблокувати себе.")
                else:
                    BlockedUser.objects.get_or_create(blocker=request.user, blocked=user_to_block)
                    messages.success(request, f"Ви заблокували {username}.")
            except User.DoesNotExist:
                messages.error(request, "Користувача з таким ім'ям не існує.")
            return redirect('messages_page')

    # Дані для відображення
    messages_received = Message.objects.filter(receiver=request.user).order_by('-created_at')
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    blocked_users = BlockedUser.objects.filter(blocker=request.user).order_by('-created_at')
    system_messages = SystemMessage.objects.filter(user=request.user).order_by('-created_at')
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'form': message_form,
        'note_form': note_form,
        'block_form': block_form,
        'messages_received': messages_received,
        'notes': notes,
        'blocked_users': blocked_users,
        'system_messages': system_messages,
        'notifications': notifications,
        'user': request.user,
    }

    return render(request, 'userspace/messages.html', context)


# -------------------------
# Позначити системне повідомлення як прочитане
# -------------------------
@login_required
def mark_message_read(request, message_id):
    """Позначає системне повідомлення як прочитане."""
    message = get_object_or_404(SystemMessage, id=message_id, user=request.user)
    if request.method == "POST":
        message.is_read = True
        message.save()
        messages.success(request, "Повідомлення позначено як прочитане.")
    return redirect('messages_page')


# -------------------------
# Блокування користувача через URL
# -------------------------
@login_required
def block_user_view(request):
    if request.method == 'POST':
        form = BlockUserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                user_to_block = User.objects.get(username=username)
                if user_to_block == request.user:
                    messages.error(request, "Ви не можете заблокувати себе.")
                else:
                    BlockedUser.objects.get_or_create(blocker=request.user, blocked=user_to_block)
                    messages.success(request, f"Ви заблокували {username}.")
            except User.DoesNotExist:
                messages.error(request, "Користувача з таким ім'ям не існує.")
    return redirect('messages_page')


# -------------------------
# Розблокування користувача
# -------------------------
@login_required
def unblock_user_view(request, user_id):
    if request.method == 'POST':
        blocked = BlockedUser.objects.filter(blocker=request.user, blocked_id=user_id)
        if blocked.exists():
            blocked.delete()
            messages.success(request, "Користувача розблоковано.")
    return redirect('messages_page')


# -------------------------
# Сторінки Хедера
# -------------------------
@login_required
def profile_page(request):
    return render(request, 'userspace/profile.html')

@login_required
def account_page(request):
    return render(request, 'userspace/account.html')

@login_required
def language_page(request):
    return render(request, 'userspace/language.html')


# -------------------------
# Промокоди
# -------------------------
PROMO_CODES = {
    'WELCOME100': {'horseshoes': 100000, 'silver_wings': 0},
    'ONE': {'horseshoes': 1000, 'silver_wings': 0, 'once': True},
}

USED_PROMO_CODES = set()

@login_required
def subscription_page(request):
    user = request.user
    promo_message = None
    promo_used = False

    if request.method == "POST" and 'promo_code' in request.POST:
        code = request.POST.get('promo_code', '').upper()

        if code in PROMO_CODES:
            if code in USED_PROMO_CODES:
                promo_message = f"Промокод {code} вже використаний!"
                promo_used = True
            else:
                # Додаємо валюту
                horseshoes_added = PROMO_CODES[code]['horseshoes']
                wings_added = PROMO_CODES[code]['silver_wings']
                user.profile.horseshoes += horseshoes_added
                user.profile.silver_wings += wings_added
                user.profile.save()

                promo_message = f"Промокод {code} активовано! Ви отримали валюту."

                # Створюємо сповіщення
                Notification.objects.create(
                    user=user,
                    text=f"Ви активували промокод {code}! Вам зараховано "
                         f"{horseshoes_added} Срібних Підков і {wings_added} Срібних Пір'їв."
                )

                # Якщо код одноразовий
                if PROMO_CODES[code].get('once', False):
                    USED_PROMO_CODES.add(code)
        else:
            promo_message = "Невірний промокод."

    # Отримуємо сповіщення для вкладки
    notifications = Notification.objects.filter(user=user).order_by('-created_at')

    context = {
        'promo_message': promo_message,
        'promo_used': promo_used,
        'notifications': notifications,
    }
    return render(request, 'userspace/subscription.html', context)


# -------------------------
# Сторінки з кіньми
# -------------------------
@login_required
def horses_page(request):
    # Куплені коні користувача
    user_horses = Horse.objects.filter(owner=request.user, status='user')
    return render(request, 'userspace/horses.html', {'user_horses': user_horses})

@login_required
def equestrian_page(request):
    return render(request, 'userspace/equestrian.html')

# -------------------------
# Ринок
# -------------------------
@login_required
def market_view(request):
    horses = Horse.objects.filter(status='market')
    return render(request, 'userspace/trade.html', {'horses': horses})

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
def manage_complex(request):
    complex_obj, created = EquestrianComplex.objects.get_or_create(owner=request.user)

    if request.method == 'POST':
        form = EquestrianComplexForm(request.POST, instance=complex_obj)
        if form.is_valid():
            form.save()
            return redirect('manage_complex')
    else:
        form = EquestrianComplexForm(instance=complex_obj)

    return render(request, 'userspace/equestrian.html', {'form': form, 'complex': complex_obj})




@login_required
def equestrian_page(request):
    user = request.user
    search_query = request.GET.get('search', '')

    # Отримати власний комплекс або None
    complex_obj = EquestrianComplex.objects.filter(owner=user).first()
    has_complex = complex_obj is not None

    # Форми
    complex_form = EquestrianComplexForm(instance=complex_obj)
    rating_form = RatingForm()

    # Отримати ВСІ комплекси для відображення в останньому розділі
    all_complexes = EquestrianComplex.objects.all()

    # Пошук по всіх комплексах (не тільки інших)
    if search_query:
        all_complexes = all_complexes.filter(
            Q(name__icontains=search_query) |
            Q(owner__username__icontains=search_query)
        )

    # POST обробка
    if request.method == 'POST':
        # 🎯 СТВОРЕННЯ КОМПЛЕКСУ
        if 'create_complex' in request.POST and not has_complex:
            try:
                # Створюємо комплекс з default значеннями
                EquestrianComplex.objects.create(
                    owner=user,
                    name=f"Комплекс {user.username}",
                    location='forest',
                    prestige=0
                )
                messages.success(request, "Комплекс успішно створено!")
                return redirect('equestrian_page')
            except Exception as e:
                messages.error(request, f"Помилка при створенні комплексу: {str(e)}")
                return redirect('equestrian_page')

        # 📝 РЕДАГУВАННЯ існуючого комплексу
        elif 'create_complex' in request.POST and has_complex:
            complex_form = EquestrianComplexForm(request.POST, instance=complex_obj)
            if complex_form.is_valid():
                complex_form.save()
                messages.success(request, "Комплекс оновлено!")
                return redirect('equestrian_page')

        # ⭐ ОЦІНКА іншого комплексу
        elif 'rating_submit' in request.POST:
            rating_form = RatingForm(request.POST)
            complex_id = request.POST.get('complex_id')
            target_complex = get_object_or_404(EquestrianComplex, id=complex_id)

            if rating_form.is_valid():
                rating_value = rating_form.cleaned_data['rating']
                if target_complex.owner != user:
                    ComplexRating.objects.update_or_create(
                        complex=target_complex,
                        user=user,
                        defaults={'rating': rating_value}
                    )
                    messages.success(request, f"Ви оцінили комплекс {target_complex.name}!")
                else:
                    messages.error(request, "Власник не може оцінювати свій комплекс.")
            return redirect('equestrian_page')

    # Середній рейтинг власного комплексу
    average_rating = None
    if has_complex and complex_obj.ratings.exists():
        average_rating = round(complex_obj.ratings.aggregate(Avg('rating'))['rating__avg'], 2)

    # Обчислити середній рейтинг для всіх комплексів
    for c in all_complexes:
        if c.ratings.exists():
            c.avg_rating = round(c.ratings.aggregate(Avg('rating'))['rating__avg'], 2)
        else:
            c.avg_rating = None

    # Отримати інші комплекси для пошукового розділу
    other_complexes = all_complexes.exclude(owner=user) if search_query else []

    context = {
        'complex_obj': complex_obj,
        'has_complex': has_complex,
        'complex_form': complex_form,
        'rating_form': rating_form,
        'average_rating': average_rating,
        'all_complexes': all_complexes,  # Всі комплекси для останнього розділу
        'other_complexes': other_complexes,  # Результати пошуку
        'search_query': search_query,
        'user': user,
    }

    return render(request, 'userspace/equestrian.html', context)


@login_required
def skip_tutorial(request):
    request.user.profile.is_new_user = False
    request.user.profile.save()
    return redirect('dashboard')


@login_required
def start_tutorial(request):
    # Можеш тут просто перенаправити на дашборд після "туторіалу"
    request.user.profile.is_new_user = False
    request.user.profile.save()
    return redirect('dashboard')




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
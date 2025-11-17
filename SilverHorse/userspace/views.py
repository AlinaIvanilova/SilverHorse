from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models  # <- для aggregate (Avg, Sum тощо)

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



# -------------------------
# Дашборд
# -------------------------
@login_required
def dashboard_view(request):
    return render(request, 'userspace/dashboard.html')


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
    'WELCOME100': {'horseshoes': 100, 'silver_wings': 0},
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

    # Отримуємо комплекс користувача
    try:
        complex_obj = EquestrianComplex.objects.get(owner=user)
        has_complex = True
    except EquestrianComplex.DoesNotExist:
        complex_obj = None
        has_complex = False

    # Форми завжди створюємо
    complex_form = EquestrianComplexForm(instance=complex_obj)
    rating_form = RatingForm()

    if request.method == 'POST':
        if 'create_complex' in request.POST:
            # Створення / редагування комплексу
            complex_form = EquestrianComplexForm(request.POST, instance=complex_obj)
            if complex_form.is_valid():
                complex_obj = complex_form.save(commit=False)
                complex_obj.owner = user
                complex_obj.save()
                messages.success(request, "Комплекс створено / оновлено!")
                return redirect('equestrian_page')

        elif 'rating_submit' in request.POST and complex_obj:
            # Форма рейтингу
            rating_form = RatingForm(request.POST)
            if rating_form.is_valid():
                rating_value = rating_form.cleaned_data['rating']
                # Власник не може оцінювати свій комплекс
                if complex_obj.owner != user:
                    ComplexRating.objects.update_or_create(
                        complex=complex_obj,
                        user=user,
                        defaults={'rating': rating_value}
                    )
                    messages.success(request, "Ваша оцінка збережена!")
                else:
                    messages.error(request, "Власник не може оцінювати свій комплекс.")
                return redirect('equestrian_page')

    # Середній рейтинг комплексу
    average_rating = None
    if has_complex and complex_obj.ratings.exists():
        average_rating = round(
            complex_obj.ratings.aggregate(models.Avg('rating'))['rating__avg'], 2
        )

    context = {
        'complex_obj': complex_obj,
        'has_complex': has_complex,
        'complex_form': complex_form,
        'rating_form': rating_form,
        'average_rating': average_rating,
    }
    return render(request, 'userspace/equestrian.html', context)


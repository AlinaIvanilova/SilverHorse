from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Message, Note, BlockedUser, SystemMessage
from .forms import MessageForm, NoteForm, BlockUserForm
from .models import Notification
from .models import Horse


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
                messages.error(request, "Користувача з таким ім’ям не існує.")
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
                messages.error(request, "Користувача з таким ім’ям не існує.")
            return redirect('messages_page')

    # Дані для відображення
    messages_received = Message.objects.filter(receiver=request.user).order_by('-created_at')
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    blocked_users = BlockedUser.objects.filter(blocker=request.user).order_by('-created_at')
    system_messages = SystemMessage.objects.filter(user=request.user).order_by('-created_at')
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')  # ось сюди додано

    context = {
        'form': message_form,
        'note_form': note_form,
        'block_form': block_form,
        'messages_received': messages_received,
        'notes': notes,
        'blocked_users': blocked_users,
        'system_messages': system_messages,
        'notifications': notifications,  # обов’язково для вкладки Сповіщення
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
                messages.error(request, "Користувача з таким ім’ям не існує.")
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
def profile_page(request):
    return render(request, 'userspace/profile.html')

def account_page(request):
    return render(request, 'userspace/account.html')

def language_page(request):
    return render(request, 'userspace/language.html')


# -------------------------
# Промокоди
# -------------------------
# Якщо промокод одноразовий — додаємо ключ 'once': True
PROMO_CODES = {
    'WELCOME100': {'horseshoes': 100, 'silver_wings': 0},
    'ONE': {'horseshoes': 1000, 'silver_wings': 0, 'once': True},
}

# Зберігаємо вже використані одноразові промокоди
USED_PROMO_CODES = set()

@login_required
def subscription_page(request):
    user = request.user
    promo_message = None
    promo_used = False  # для шаблону

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

                # Створюємо сповіщення у вкладці "Сповіщення"
                Notification.objects.create(
                    user=user,
                    text=f"Ви активували промокод {code}! Вам зараховано "
                         f"{horseshoes_added} Срібних Підков і {wings_added} Срібних Пір'їв."
                )

                # Якщо код одноразовий — додаємо у список використаних
                if PROMO_CODES[code].get('once', False):
                    USED_PROMO_CODES.add(code)
        else:
            promo_message = "Невірний промокод."

    # Отримуємо сповіщення для вкладки
    notifications = Notification.objects.filter(user=user).order_by('-created_at')

    context = {
        'user_horseshoes': user.profile.horseshoes,
        'user_silver_wings': user.profile.silver_wings,
        'promo_message': promo_message,
        'promo_used': promo_used,
        'notifications': notifications,  # для вкладки Сповіщення
    }
    return render(request, 'userspace/subscription.html', context)




def horses_page(request):
    return render(request, 'userspace/horses.html')

def equestrian_page(request):
    return render(request, 'userspace/equestrian.html')

# Відповідає за ринок
def market_view(request):
    horses = Horse.objects.filter(status='market')  # всі коні на ринку
    return render(request, 'userspace/trade.html', {'horses': horses})
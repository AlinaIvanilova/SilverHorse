# userspace/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Message, Note, BlockedUser, SystemMessage
from .forms import MessageForm, NoteForm, BlockUserForm


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

    # -------------------------
    # Відправлення повідомлення
    # -------------------------
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

                # Створюємо повідомлення
                Message.objects.create(sender=request.user, receiver=receiver, text=text)
                messages.success(request, f"Повідомлення відправлено користувачу {receiver_username}.")

            except User.DoesNotExist:
                messages.error(request, "Користувача з таким ім’ям не існує.")
            return redirect('messages_page')

    # -------------------------
    # Створення нотатки
    # -------------------------
    if request.method == 'POST' and 'note-submit' in request.POST:
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.user = request.user
            note.save()
            messages.success(request, "Нотатка збережена.")
            return redirect('messages_page')

    # -------------------------
    # Блокування користувача
    # -------------------------
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

    # -------------------------
    # Дані для шаблону
    # -------------------------
    messages_received = Message.objects.filter(receiver=request.user).order_by('-created_at')
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    blocked_users = BlockedUser.objects.filter(blocker=request.user).order_by('-created_at')

    # -------------------------
    # Перше системне повідомлення (створюється автоматично при першому вході)
    # -------------------------
    if not SystemMessage.objects.filter(user=request.user).exists():
        SystemMessage.objects.create(
            user=request.user,
            title="Вітаємо на Silver Horse!",
            content="Дякуємо за успішну реєстрацію 💫. "
                    "Тепер ви можете надсилати повідомлення, вести нотатки, "
                    "керувати чорним списком і отримувати новини від системи."
        )

    # -------------------------
    # Отримання системних повідомлень
    # -------------------------
    system_messages = SystemMessage.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'userspace/messages.html', {
        'form': message_form,
        'note_form': note_form,
        'block_form': block_form,
        'messages_received': messages_received,
        'notes': notes,
        'blocked_users': blocked_users,
        'system_messages': system_messages,
        'user': request.user,
    })


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

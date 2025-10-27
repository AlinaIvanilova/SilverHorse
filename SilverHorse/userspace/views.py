# userspace/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from .models import Message
from .forms import MessageForm

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
# Сторінка повідомлень (вкладки)
# -------------------------
@login_required
def messages_page(request):
    # Форма для відправки повідомлення
    form = MessageForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # Отримуємо користувача з імені, яке ввів користувач
        receiver = form.cleaned_data['receiver_username']
        message = Message(
            sender=request.user,
            receiver=receiver,
            text=form.cleaned_data['text']
        )
        message.save()
        return redirect('messages_page')

    # Повідомлення, де користувач є отримувачем
    messages_received = Message.objects.filter(receiver=request.user).order_by('-created_at')

    return render(request, 'userspace/messages.html', {
        'form': form,
        'messages_received': messages_received,
        'user': request.user,
    })


# -------------------------
# Окрема сторінка "Написати повідомлення"
# -------------------------
@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = Message(
                sender=request.user,
                receiver=form.cleaned_data['receiver_username'],  # <-- отримуємо User-об’єкт
                text=form.cleaned_data['text']
            )
            message.save()
            return redirect('messages_page')
    else:
        form = MessageForm()

    return render(request, 'userspace/send_message.html', {'form': form})

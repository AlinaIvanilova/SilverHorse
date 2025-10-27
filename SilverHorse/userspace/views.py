from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from .models import Message, Note
from .forms import MessageForm, NoteForm

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
# Сторінка повідомлень і блокноту (вкладки)
# -------------------------
@login_required
def messages_page(request):
    # Форма повідомлення
    message_form = MessageForm(request.POST or None, prefix='msg')
    # Форма нотатки
    note_form = NoteForm(request.POST or None, prefix='note')

    # Обробка відправки повідомлення
    if request.method == 'POST' and 'msg-submit' in request.POST:
        if message_form.is_valid():
            receiver = message_form.cleaned_data['receiver_username']
            message = Message(
                sender=request.user,
                receiver=receiver,
                text=message_form.cleaned_data['text']
            )
            message.save()
            return redirect('messages_page')

    # Обробка створення нотатки
    if request.method == 'POST' and 'note-submit' in request.POST:
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.user = request.user
            note.save()
            return redirect('messages_page')

    # Повідомлення для користувача
    messages_received = Message.objects.filter(receiver=request.user).order_by('-created_at')
    # Нотатки для користувача
    notes = Note.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'userspace/messages.html', {
        'form': message_form,
        'note_form': note_form,
        'messages_received': messages_received,
        'notes': notes,
        'user': request.user,
    })

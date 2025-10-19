from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'main/home.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # Перенаправляємо на dashboard після успішного входу
            return redirect('dashboard')
        else:
            return render(request, 'main/login.html', {'error': 'Невірний логін або пароль'})
    return render(request, 'main/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            return render(request, 'main/register.html', {'error': 'Паролі не співпадають'})

        if User.objects.filter(username=username).exists():
            return render(request, 'main/register.html', {'error': 'Користувач з таким ім’ям вже існує'})

        # Створюємо нового користувача
        user = User.objects.create_user(username=username, password=password1)
        return redirect('login')

    return render(request, 'main/register.html')

# Приклад dashboard view у userspace/views.py
@login_required
def dashboard_view(request):
    return render(request, 'userspace/dashboard.html')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def dashboard_view(request):
    return render(request, 'userspace/dashboard.html')


def logout_view(request):
    logout(request)
    return redirect('home')  # Після виходу користувач повернеться на головну

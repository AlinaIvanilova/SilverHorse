from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def profile_page(request):
    return render(request, 'userspace/profile.html')

@login_required
def account_page(request):
    return render(request, 'userspace/account.html')

@login_required
def language_page(request):
    return render(request, 'userspace/language.html')
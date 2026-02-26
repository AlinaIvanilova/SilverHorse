# userspace/views/shelter.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def shelter_view(request):
    return render(request, 'userspace/shelter.html')
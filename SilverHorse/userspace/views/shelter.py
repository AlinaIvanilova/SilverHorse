# userspace/views/shelter.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Horse

@login_required
def shelter_view(request):
    shelter_horses = Horse.objects.filter(status='shelter')
    return render(request, 'userspace/shelter.html', {'horses': shelter_horses})

@login_required
def send_to_shelter(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id, owner=request.user, status='user')
    profile = request.user.profile
    profile.horseshoes += 500
    profile.save()
    horse.status = 'shelter'
    horse.owner = None
    horse.save()
    messages.success(request, f"Ви відправили коня {horse.name} до притулку та отримали 500 підков.")
    return redirect('horses_page')
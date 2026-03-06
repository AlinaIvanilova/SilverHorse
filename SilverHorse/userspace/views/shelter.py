# userspace/views/shelter.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Horse, HorsePet

@login_required
def shelter_view(request):
    shelter_horses = Horse.objects.filter(status='shelter')
    breeds = Horse.objects.filter(status='shelter') \
                .values_list('breed', flat=True) \
                .distinct() \
                .order_by('breed')
    horse_types = Horse.TYPE_CHOICES
    return render(request, 'userspace/shelter.html', {
        'horses': shelter_horses,
        'breeds': breeds,
        'horse_types': horse_types,
    })

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

@login_required
def pet_horse(request, horse_id):
    horse = get_object_or_404(Horse, id=horse_id, status='shelter')
    if HorsePet.objects.filter(user=request.user, horse=horse).exists():
        messages.error(request, f"Ви вже гладили коня {horse.name}. Приходьте завтра!")
        return redirect('horse_detail', horse_id=horse.id)

    HorsePet.objects.create(user=request.user, horse=horse)
    profile = request.user.profile
    profile.horseshoes += 10
    profile.save()
    messages.success(request, f"Ви погладили {horse.name} і отримали 10 Срібних Підков!")
    return redirect('horse_detail', horse_id=horse.id)